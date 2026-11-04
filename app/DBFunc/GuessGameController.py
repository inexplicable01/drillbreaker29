import json
import re
import traceback
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from app.config import GuessGameConfig as GC, PENDING, RECENTLYSOLD
from app.DBModels.BriefListing import BriefListing
from app.DBModels.GuessGame import GameListing, GameGuess, GameRun
from app.EmailHelper.EmailSender import send_email
from app.extensions import db
from app.useful_func import print_and_log
from app.ZillowAPI.ZillowAPICall import SearchZillowByZPID

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$')
INSTAGRAM_RE = re.compile(r'^[A-Za-z0-9._]{1,30}$')
MIN_GUESS = 10_000
MAX_GUESS = 100_000_000
GAME_HOME_TYPES = ['SINGLE_FAMILY', 'TOWNHOUSE', 'CONDO']


def _money(value):
    return f"${value:,.0f}" if value is not None else "n/a"


def _fmt_num(value):
    # 2.0 -> "2", 2.5 -> "2.5"
    return f"{value:g}" if value is not None else "?"


def _history_event(propertydata, keyword):
    """Most recent priceHistory event whose name contains keyword (Zillow lists newest first)."""
    for event in propertydata.get('priceHistory') or []:
        if keyword in str(event.get('event', '')):
            return event
    return None


HISTORY_FIELDS = ('date', 'event', 'price', 'priceChangeRate', 'pricePerSquareFoot', 'source')


def _listing_history(propertydata):
    """Zillow priceHistory as returned, newest first (only the fields we display)."""
    return [{k: event.get(k) for k in HISTORY_FIELDS} for event in propertydata.get('priceHistory') or []]


def _photo_urls(propertydata, limit=15):
    urls = []
    for photo in propertydata.get('originalPhotos') or propertydata.get('photos') or []:
        jpegs = (photo.get('mixedSources') or {}).get('jpeg') or []
        if not jpegs:
            continue
        sized = [j for j in jpegs if j.get('width') == 1024]
        urls.append((sized or jpegs)[-1]['url'])
        if len(urls) >= limit:
            break
    return urls


def parse_guess_price(raw):
    """Accepts 750000, "750,000", "$750k", "1.2m". Returns int or None."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = str(raw).strip().lower().replace('$', '').replace(',', '').replace(' ', '')
        multiplier = 1
        if text.endswith('k'):
            multiplier, text = 1_000, text[:-1]
        elif text.endswith('m'):
            multiplier, text = 1_000_000, text[:-1]
        try:
            value = float(text) * multiplier
        except ValueError:
            return None
    if not (MIN_GUESS <= value <= MAX_GUESS):
        return None
    return int(round(value))


class GuessGameController():

    def __init__(self):
        self.api_calls = 0

    def _lookup(self, zpid):
        self.api_calls += 1
        return SearchZillowByZPID(zpid)

    # ---------- queries ----------

    def get_listing(self, listing_id):
        return db.session.get(GameListing, listing_id)

    def all_listings(self):
        return GameListing.query.order_by(GameListing.created_at.desc()).all()

    def recent_runs(self, limit=20):
        return GameRun.query.order_by(GameRun.started_at.desc()).limit(limit).all()

    def ranked_guesses(self, listing):
        return listing.guesses.order_by(GameGuess.rank.is_(None), GameGuess.rank, GameGuess.created_at).all()

    # ---------- guesses ----------

    def submit_guess(self, listing, data):
        """Returns (http_status, payload dict)."""
        if listing.status != 'open':
            return 409, {'ok': False, 'error': 'Guessing is closed for this home.'}

        name = str(data.get('name') or '').strip()
        email = str(data.get('email') or '').strip().lower()
        instagram = str(data.get('instagram') or '').strip().lstrip('@')
        guessed_price = parse_guess_price(data.get('guess'))

        errors = {}
        if not name or len(name) > 120:
            errors['name'] = 'Please enter your name.'
        if not EMAIL_RE.match(email) or len(email) > 255:
            errors['email'] = 'Please enter a valid email address.'
        if guessed_price is None:
            errors['guess'] = f'Please enter a sale price between {_money(MIN_GUESS)} and {_money(MAX_GUESS)}.'
        if instagram and not INSTAGRAM_RE.match(instagram):
            errors['instagram'] = 'That Instagram handle doesn\'t look right.'
        if errors:
            return 400, {'ok': False, 'error': 'Please fix the highlighted fields.', 'fields': errors}

        if listing.guesses.filter(GameGuess.email == email).first():
            return 409, {'ok': False, 'error': 'You\'ve already locked in a guess for this home.'}

        guess = GameGuess(listing_id=listing.id, name=name, email=email,
                          guessed_price=guessed_price, instagram=instagram or None)
        db.session.add(guess)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 409, {'ok': False, 'error': 'You\'ve already locked in a guess for this home.'}
        return 201, {'ok': True, 'guess': guessed_price,
                     'message': f'Your guess of {_money(guessed_price)} is locked in. Good luck!'}

    # ---------- daily run ----------

    def should_pick_today(self, today=None):
        if GC.GAME_FREQUENCY == 'weekly':
            return (today or datetime.now()).weekday() == GC.GAME_WEEKDAY
        return True

    def run_daily(self, force_pick=False):
        self.api_calls = 0
        run = GameRun()
        db.session.add(run)
        db.session.commit()
        print_and_log(f"[GuessGame] run {run.id} started {run.started_at}")
        try:
            checked, scored, expired = self.check_open_listings()
            run.checked, run.scored, run.expired = checked, scored, expired

            picks = []
            if force_pick or self.should_pick_today():
                picks = self.pick_listings()
                if picks:
                    if not send_email(self._package_subject(picks), GC.PACKAGE_RECIPIENT, self.package_email_html(picks)):
                        raise RuntimeError('Game package email failed to send')
            run.picks = len(picks)
            run.status = 'success'
            run.message = (f"Picked {len(picks)}: " + '; '.join(p.address for p in picks)) if picks else \
                ('No eligible homes found' if (force_pick or self.should_pick_today()) else 'Not a pick day')
        except Exception as e:
            db.session.rollback()
            run.status = 'failed'
            run.message = f"{e}\n{traceback.format_exc()}"
            send_email('Guess the Price: daily run FAILED', GC.ADMIN_EMAIL,
                       f"<p>Run {run.id} failed.</p><pre>{run.message}</pre>")
        run.api_calls = self.api_calls
        run.finished_at = datetime.utcnow()
        db.session.add(run)
        db.session.commit()
        print_and_log(f"[GuessGame] run {run.id} {run.status}: picks={run.picks} checked={run.checked} "
                      f"scored={run.scored} expired={run.expired} api_calls={run.api_calls} | {run.message.splitlines()[0] if run.message else ''}")
        return run

    # ---------- picking ----------

    def pick_listings(self):
        now = datetime.utcnow()
        used = select(GameListing.zpid)
        candidates = (BriefListing.query
                      .filter(BriefListing.homeStatus == PENDING,
                              BriefListing.homeType.in_(GAME_HOME_TYPES),
                              BriefListing.pendday.between((now - timedelta(days=GC.MAX_DAYS_PENDING)).timestamp(),
                                                           (now - timedelta(days=GC.MIN_DAYS_PENDING)).timestamp()),
                              BriefListing.price > 0,
                              BriefListing.bedrooms > 0,
                              BriefListing.bathrooms > 0,
                              BriefListing.livingArea > 0,
                              ~BriefListing.zpid.in_(used))
                      .order_by(func.rand())
                      .limit(GC.MAX_PICK_LOOKUPS_PER_RUN)
                      .all())

        picks = []
        for candidate in candidates:
            if len(picks) >= GC.PICKS_PER_RUN:
                break
            listing = self._build_listing(candidate.zpid)
            if listing:
                db.session.add(listing)
                db.session.commit()
                picks.append(listing)
                print_and_log(f"[GuessGame] picked {listing.address} (zpid {listing.zpid})")
        return picks

    def _build_listing(self, zpid):
        """Confirms the home on Zillow and returns an unsaved GameListing, or None if it doesn't qualify."""
        p = self._lookup(zpid)
        if not p or p.get('homeStatus') != PENDING:
            return None

        pending_event = _history_event(p, 'Pending')
        if not pending_event:
            return None
        pending_date = datetime.strptime(pending_event['date'], '%Y-%m-%d').date()
        if (datetime.utcnow().date() - pending_date).days < GC.MIN_DAYS_PENDING:
            return None

        photos = _photo_urls(p)
        beds, baths, sqft, price = p.get('bedrooms'), p.get('bathrooms'), p.get('livingArea'), p.get('price')
        if len(photos) < GC.MIN_PHOTOS or not (beds and baths and sqft and price):
            return None

        street = p.get('streetAddress') or (p.get('address') or {}).get('streetAddress')
        return GameListing(
            zpid=zpid,
            address=f"{street}, {p.get('city')}, {p.get('state')} {p.get('zipcode')}",
            list_price=int(price),
            pending_date=pending_date,
            listing_history=json.dumps(_listing_history(p)),
            beds=beds, baths=baths, sqft=int(sqft),
            photo_urls=json.dumps(photos),
            zillow_url=f"https://www.zillow.com{p['hdpUrl']}" if p.get('hdpUrl') else None,
            status='open',
        )

    def refresh_history(self, listing):
        """Re-pull listing history from Zillow (one API call)."""
        p = self._lookup(listing.zpid)
        if not p:
            return False
        listing.listing_history = json.dumps(_listing_history(p))
        db.session.commit()
        return True

    # ---------- sold tracking & scoring ----------

    def check_open_listings(self):
        checked = scored = expired = 0
        open_listings = (GameListing.query.filter_by(status='open')
                         .order_by(GameListing.last_checked_at.is_(None).desc(), GameListing.last_checked_at)
                         .all())
        for listing in open_listings:
            if checked >= GC.MAX_STATUS_CHECKS_PER_RUN:
                break
            checked += 1
            final_price, sold_date = self._sold_price(listing)
            listing.last_checked_at = datetime.utcnow()
            if final_price:
                listing.status = 'sold'
                listing.final_price = final_price
                listing.sold_date = sold_date
                db.session.commit()
                self.score_listing(listing)
                scored += 1
            elif datetime.utcnow() - listing.created_at > timedelta(days=GC.EXPIRE_AFTER_DAYS):
                listing.status = 'expired'
                db.session.commit()
                expired += 1
                print_and_log(f"[GuessGame] expired {listing.address}")
            else:
                db.session.commit()
        return checked, scored, expired

    def _sold_price(self, listing):
        """(price, date) once sold, else (None, None). Uses the ingestion DB first to save API calls."""
        brief = db.session.get(BriefListing, listing.zpid)
        if brief and brief.homeStatus == RECENTLYSOLD and brief.soldprice:
            sold_date = datetime.utcfromtimestamp(brief.dateSold / 1000).date() if brief.dateSold else None
            if sold_date is None or sold_date >= listing.created_at.date() - timedelta(days=1):
                return int(brief.soldprice), sold_date

        p = self._lookup(listing.zpid)
        if not p or p.get('homeStatus') != RECENTLYSOLD:
            return None, None
        sold_event = _history_event(p, 'Sold')
        price = (sold_event or {}).get('price') or p.get('lastSoldPrice') or p.get('price')
        sold_date = datetime.strptime(sold_event['date'], '%Y-%m-%d').date() if sold_event else None
        return (int(price), sold_date) if price else (None, None)

    def score_listing(self, listing):
        guesses = listing.guesses.all()
        for g in guesses:
            g.error = abs(g.guessed_price - listing.final_price)
        guesses.sort(key=lambda g: (g.error, g.created_at))
        for i, g in enumerate(guesses, start=1):
            g.rank = i
        listing.scored_at = datetime.utcnow()
        db.session.commit()
        print_and_log(f"[GuessGame] scored {listing.address}: sold {_money(listing.final_price)}, {len(guesses)} guesses")

        send_email(f"Guess the Price results: {listing.address} sold for {_money(listing.final_price)}",
                   GC.ADMIN_EMAIL, self.results_email_html(listing, guesses))
        if GC.NOTIFY_ENTRANTS:
            for g in guesses:
                send_email(f"The results are in: {listing.address}", g.email,
                           self.entrant_email_html(listing, g, guesses[0], len(guesses)))

    # ---------- emails ----------

    def game_url(self, listing):
        return GC.GAME_PAGE_URL.format(id=listing.id)

    def open_listings(self):
        return GameListing.query.filter_by(status='open').order_by(GameListing.created_at.desc()).all()

    def public_dict(self, listing):
        """What wayber.ai may show publicly: no entrant data beyond the count."""
        return {
            'id': listing.id,
            'address': listing.address,
            'status': listing.status,
            'list_price': listing.list_price,
            'beds': listing.beds,
            'baths': listing.baths,
            'sqft': listing.sqft,
            'pending_date': listing.pending_date.isoformat() if listing.pending_date else None,
            'days_pending': listing.days_pending(),
            'listing_history': listing.history,
            'photos': listing.photos,
            'guess_count': listing.guesses.count(),
            'final_price': listing.final_price if listing.status == 'sold' else None,
            'sold_date': listing.sold_date.isoformat() if listing.sold_date else None,
            'accepting_guesses': listing.status == 'open',
            'game_url': self.game_url(listing),
            'created_at': listing.created_at.isoformat() + 'Z',
        }

    def reel_script(self, listing):
        city = listing.address.split(', ')[1] if ', ' in listing.address else 'Washington'
        days = listing.days_pending()
        beds = _fmt_num(listing.beds)
        hooks = [
            f"This {beds}-bed home in {city} has been pending for {days} days. What do you think it actually sold for?",
            f"Pending for {days} days in {city}. Did this home sell over or under asking? You tell me.",
            f"Can you guess what this {city} home really sold for? Most people can't.",
        ]
        ppsf = round(listing.list_price / listing.sqft) if listing.sqft else None
        facts = [
            f"{beds} beds, {_fmt_num(listing.baths)} baths, {listing.sqft:,} square feet.",
            f"Listed at {_money(listing.list_price)}" + (f", about {_money(ppsf)} a square foot." if ppsf else "."),
            f"It went pending on {listing.pending_date:%B} {listing.pending_date.day} and still hasn't closed.",
        ]
        return {
            'hook': hooks[listing.id % len(hooks)],
            'facts': facts,
            'guess_line': "Guess the sale price in the comments, then lock in your official guess at the link in bio to win.",
            'cta': "Follow Wayber so you catch the reveal when it closes.",
        }

    def _package_subject(self, picks):
        return f"Guess the Price game package: {len(picks)} new home{'s' if len(picks) > 1 else ''} ({datetime.now():%b %d})"

    def package_email_html(self, picks):
        sections = []
        for listing in picks:
            script = self.reel_script(listing)
            photos = listing.photos[:10]
            thumbs = ''.join(f'<a href="{u}"><img src="{u}" width="160" style="margin:2px;border-radius:4px"></a>' for u in photos[:4])
            photo_links = ''.join(f'<li><a href="{u}">Photo {i}</a></li>' for i, u in enumerate(photos, start=1))
            facts = ''.join(f'<li>{f}</li>' for f in script['facts'])
            history_rows = ''.join(
                f"<tr><td>{e.get('date')}</td><td>{e.get('event')}</td><td>{_money(e.get('price')) if e.get('price') is not None else 'N/A'}</td>"
                f"<td>{format(e['priceChangeRate'], '.2%') if e.get('priceChangeRate') is not None else 'N/A'}</td>"
                f"<td>{('$' + str(e['pricePerSquareFoot']) + '/sqft') if e.get('pricePerSquareFoot') is not None else 'N/A'}</td>"
                f"<td>{e.get('source') or ''}</td></tr>" for e in listing.history)
            sections.append(f"""
<div style="border:1px solid #ddd;border-radius:8px;padding:16px;margin-bottom:20px">
  <h2 style="margin-top:0">{listing.address}</h2>
  <p><b>List price:</b> {_money(listing.list_price)}<br>
     <b>Days pending:</b> {listing.days_pending()} (since {listing.pending_date:%b %d, %Y})<br>
     <b>Beds / baths / sqft:</b> {_fmt_num(listing.beds)} / {_fmt_num(listing.baths)} / {listing.sqft:,}</p>
  <p><b>Listing history:</b></p>
  <table border="1" cellpadding="4" style="border-collapse:collapse;font-size:13px">
    <tr><th>Date</th><th>Event</th><th>Price</th><th>Price Change Rate</th><th>Price/Sqft</th><th>Source</th></tr>{history_rows or '<tr><td colspan="6">No price history available.</td></tr>'}</table>
  <p><b>Game page:</b> <a href="{self.game_url(listing)}">{self.game_url(listing)}</a><br>
     <b>Zillow:</b> <a href="{listing.zillow_url}">{listing.zillow_url}</a></p>
  <div>{thumbs}</div>
  <p><b>Photos ({len(photos)}):</b></p><ol>{photo_links}</ol>
  <h3>Reel script (20&ndash;30 sec)</h3>
  <p><b>Hook:</b> {script['hook']}</p>
  <p><b>Three quick facts:</b></p><ol>{facts}</ol>
  <p><b>Guess:</b> {script['guess_line']}</p>
  <p><b>CTA:</b> {script['cta']}</p>
</div>""")
        return f"<div style='font-family:Arial,sans-serif;max-width:720px'><h1>Guess the Price: today's homes</h1>{''.join(sections)}</div>"

    def results_email_html(self, listing, ranked):
        diff = listing.final_price - listing.list_price if listing.list_price else None
        header = f"""
<h2>{listing.address}</h2>
<p><b>Sold for:</b> {_money(listing.final_price)} (listed at {_money(listing.list_price)}{f', {"+" if diff >= 0 else "-"}{_money(abs(diff))}' if diff is not None else ''})<br>
<b>Guesses:</b> {len(ranked)}<br>
<b>Game page:</b> <a href="{self.game_url(listing)}">{self.game_url(listing)}</a></p>"""
        if not ranked:
            return f"<div style='font-family:Arial,sans-serif'>{header}<p>No guesses were entered for this home.</p></div>"
        w = ranked[0]
        rows = ''.join(
            f"<tr><td>{g.rank}</td><td>{g.name}</td><td>{g.email}</td><td>{'@' + g.instagram if g.instagram else ''}</td>"
            f"<td>{_money(g.guessed_price)}</td><td>{_money(g.error)}</td></tr>" for g in ranked[:5])
        return f"""<div style='font-family:Arial,sans-serif'>{header}
<p><b>Winner:</b> {w.name} ({w.email}{', @' + w.instagram if w.instagram else ''}) guessed {_money(w.guessed_price)}, off by {_money(w.error)}.</p>
<table border="1" cellpadding="6" style="border-collapse:collapse">
<tr><th>Rank</th><th>Name</th><th>Email</th><th>Instagram</th><th>Guess</th><th>Off by</th></tr>{rows}</table></div>"""

    def entrant_email_html(self, listing, guess, winner, total):
        return f"""<div style='font-family:Arial,sans-serif;max-width:600px'>
<p>Hi {guess.name},</p>
<p>The results are in for <b>{listing.address}</b>. It sold for <b>{_money(listing.final_price)}</b>.</p>
<p>Your guess was {_money(guess.guessed_price)}, off by {_money(guess.error)}. You placed #{guess.rank} of {total}.
{'<b>You won!</b> We&#39;ll be in touch shortly.' if guess.id == winner.id else f'The closest guess was {_money(winner.guessed_price)}.'}</p>
<p>Thinking about buying or selling? Wayber helps Washington buyers and sellers keep more of their money. Just reply to this email to talk with us.</p>
<p>Watch for the next round on Instagram!</p>
<p>Wayber Team</p></div>"""


guessgamecontroller = GuessGameController()
