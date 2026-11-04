import csv
import hmac
import io
from functools import wraps

from flask import Blueprint, render_template, request, jsonify, Response, abort, redirect, url_for

from app.config import GuessGameConfig as GC
from app.DBFunc.GuessGameController import guessgamecontroller, _money, _fmt_num
from app.DBModels.GuessGame import GameGuess

guessgame_bp = Blueprint('guessgame_bp', __name__)


def _password_ok(supplied):
    return bool(GC.ADMIN_PASSWORD) and supplied is not None and hmac.compare_digest(supplied, GC.ADMIN_PASSWORD)


def admin_required(view):
    """HTTP basic auth; any username, password = GAME_ADMIN_PASSWORD."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth or not _password_ok(auth.password):
            return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Guess the Price admin"'})
        return view(*args, **kwargs)
    return wrapped


@guessgame_bp.app_template_filter('money')
def money_filter(value):
    return _money(value)


@guessgame_bp.app_template_filter('num')
def num_filter(value):
    return _fmt_num(value)


# ---------- public ----------

@guessgame_bp.route('/game/<int:listing_id>', methods=['GET'])
def game_page(listing_id):
    listing = guessgamecontroller.get_listing(listing_id)
    if not listing:
        abort(404)
    return render_template('GuessGame/Game.html', listing=listing,
                           guess_count=listing.guesses.count())


@guessgame_bp.after_request
def add_cors_headers(response):
    # wayber.ai hosts the public game and calls these endpoints from the browser
    origin = request.headers.get('Origin')
    if request.path.startswith('/api/game') and origin in GC.ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers['Vary'] = 'Origin'
    return response


@guessgame_bp.route('/api/game/open', methods=['GET'])
def api_open_games():
    return jsonify({'games': [guessgamecontroller.public_dict(l) for l in guessgamecontroller.open_listings()]})


@guessgame_bp.route('/api/game/<int:listing_id>', methods=['GET'])
def api_game(listing_id):
    listing = guessgamecontroller.get_listing(listing_id)
    if not listing:
        return jsonify({'ok': False, 'error': 'Game not found.'}), 404
    return jsonify(guessgamecontroller.public_dict(listing))


@guessgame_bp.route('/api/game/<int:listing_id>/guess', methods=['POST', 'OPTIONS'])
def submit_guess(listing_id):
    if request.method == 'OPTIONS':  # CORS preflight; headers added in after_request
        return '', 204
    listing = guessgamecontroller.get_listing(listing_id)
    if not listing:
        return jsonify({'ok': False, 'error': 'Game not found.'}), 404
    if not request.is_json:
        return jsonify({'ok': False, 'error': 'Send the guess as application/json.'}), 415
    status, payload = guessgamecontroller.submit_guess(listing, request.get_json(silent=True) or {})
    return jsonify(payload), status


# ---------- scheduled task ----------

@guessgame_bp.route('/game/tasks/daily', methods=['POST'])
def run_daily_task():
    if not _password_ok(request.headers.get('X-Game-Key')):
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    force_pick = (request.get_json(silent=True) or {}).get('force_pick', False)
    run = guessgamecontroller.run_daily(force_pick=bool(force_pick))
    return jsonify({'ok': run.status == 'success', 'run_id': run.id, 'status': run.status,
                    'picks': run.picks, 'checked': run.checked, 'scored': run.scored,
                    'expired': run.expired, 'api_calls': run.api_calls,
                    'message': run.message}), 200 if run.status == 'success' else 500


# ---------- admin ----------

@guessgame_bp.route('/game/admin', methods=['GET'])
@admin_required
def admin():
    listings = guessgamecontroller.all_listings()
    rounds = []
    for listing in listings:
        ranked = guessgamecontroller.ranked_guesses(listing)
        rounds.append({'listing': listing, 'guess_count': len(ranked),
                       'winner': ranked[0] if listing.status == 'sold' and ranked else None})
    return render_template('GuessGame/Admin.html', rounds=rounds, runs=guessgamecontroller.recent_runs(),
                           config=GC)


@guessgame_bp.route('/game/admin/<int:listing_id>', methods=['GET'])
@admin_required
def admin_round(listing_id):
    listing = guessgamecontroller.get_listing(listing_id)
    if not listing:
        abort(404)
    return render_template('GuessGame/AdminRound.html', listing=listing,
                           guesses=guessgamecontroller.ranked_guesses(listing),
                           script=guessgamecontroller.reel_script(listing))


@guessgame_bp.route('/game/admin/run', methods=['POST'])
@admin_required
def admin_run_now():
    guessgamecontroller.run_daily(force_pick=request.form.get('force_pick') == '1')
    return redirect(url_for('guessgame_bp.admin'))


@guessgame_bp.route('/game/admin/entrants.csv', methods=['GET'])
@admin_required
def export_entrants():
    query = GameGuess.query.order_by(GameGuess.listing_id, GameGuess.created_at)
    listing_id = request.args.get('listing_id', type=int)
    if listing_id:
        query = query.filter(GameGuess.listing_id == listing_id)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['listing_id', 'address', 'name', 'email', 'instagram', 'guessed_price',
                     'final_price', 'off_by', 'rank', 'submitted_utc'])
    for g in query.all():
        writer.writerow([g.listing_id, g.listing.address, g.name, g.email, g.instagram or '',
                         g.guessed_price, g.listing.final_price or '', g.error if g.error is not None else '',
                         g.rank or '', g.created_at.strftime('%Y-%m-%d %H:%M')])
    filename = f"guess_the_price_entrants{'_' + str(listing_id) if listing_id else ''}.csv"
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})
