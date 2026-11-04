RECENTLYSOLD="RECENTLY_SOLD"
FOR_SALE="FOR_SALE"
FOR_RENT="FOR_RENT"
PENDING="PENDING"
LIKELYSOLDWITHOUTAGENTS='LikelySoldWithoutAgents'
OTHER="OTHER"
AUCTIONITEM="AUCTIONITEM"

class SW(object):
    TOWNHOUSE = 'TOWNHOUSE'
    SINGLE_FAMILY = 'SINGLE_FAMILY'
    CONDO = 'CONDO'
    APARTMENT='APARTMENT'
    MANUFACTURED = 'MANUFACTURED'
    LOT='LOT'


class Config(object):
    # CITIES = ['Kirkland','Kenmore', 'Bothell',]
    CITIES = [
        'Shoreline', 'Bothell', 'Kenmore', 'Kirkland', 'Woodinville', 'Duvall', 'Carnation',
        'Auburn', 'Bellevue', 'Black Diamond', 'Burien', 'Clyde Hill', 'Covington', 'Des Moines', 'Enumclaw',
        'Federal Way', 'Hunts Point', 'Issaquah', 'Kenmore', 'Kent', 'Kirkland', 'Lake Forest Park', 'Maple Valley',
        'Medina', 'Mercer Island', 'Milton', 'Newcastle', 'Normandy Park', 'North Bend', 'Pacific', 'Redmond',
        'Renton', 'Sammamish', 'SeaTac', 'Seattle', 'Skykomish', 'Snoqualmie', 'Tukwila',
        'Yarrow Point'
    ]
    #
    doz_options=[1,7,14,30,90,180,360]
    plottingoptions = ['sold','pending']
    NEIGHBORHOODS = ['Ballard', 'Fremont', 'Crown Hill', 'Green Wood', 'Phinney Ridge', 'Wallingford', 'North Beach',
                     'Blue Ridge', 'Whittier Heights', 'Loyal Heights', 'Sunset Hill', 'Magnolia', 'Queen Anne']
    WRONGNEIGHBORHOODS = ['Maple Leaf', 'South Lake Union', 'Bryant', 'Laurelhurst',
                          'Madison Park', 'Madison', 'Capitol Hill', 'Roosevelt', 'Eastlake']
    SEATTLE_GAPIS_TO_NEIGH = {
        'Adams': 'Ballard',
        'Ballard': 'Ballard',
        'West Woodland': 'Ballard',
        'Loyal Heights': 'Ballard',
        'Northwest Seattle': 'Phinney Ridge and Greenlake',
        'Maple Leaf': 'Phinney Ridge and Greenlake',
        'North Beach/Blue Ridge': 'North Beach/Blue Ridge',
        'Crown Hill': 'Crown Hill',
        'Broadview': 'Broadview',
        'Wallingford': 'Wallingford',
        'Fremont': 'Fremont',
        'Northgate': 'Northgate',
        'Meadowbrook': 'North Seattle',
        'North Seattle': 'North Seattle',
        'Cedar Park': 'North Seattle',
        'Matthews Beach': 'North Seattle',
        'Northeast Seattle': 'Northeast Seattle',
        'Southeast Magnolia': 'Magnolia',
        'Olympic Hills': 'Northeast Seattle',
        'Magnolia': 'Magnolia',
        'East Queen Anne': 'Queen Anne',
        'North Queen Anne': 'Queen Anne',
        'Queen Anne': 'Queen Anne',
        'West Queen Anne': 'Queen Anne',
        'Westlake': 'Queen Anne',
        'Uptown': 'Seattle Center',
        'South Lake Union': 'Seattle Center',
        'Downtown Seattle': 'Seattle Center',
        'Yesler Terrace': 'Central District',
        'Leschi': 'Central District',
        'Minor': 'Central District',
        'Central District': 'Central District',
        'Madison Park': 'Madison Park',
        'Washington Park': 'Madison Park',
        'Madison Valley': 'Madison Park',
        'Capitol Hill': 'Capitol Hill',
        'Stevens': 'Capitol Hill',
        'Miller Park': 'Capitol Hill',
        'Eastlake': 'Eastlake',
        'Greater Duwamish': 'Beacon Hill',
        'Rainier Vista': 'Beacon Hill',
        'Mount Baker': 'Rainier Valley',
        'Rainier Valley': 'Rainier Valley',
        'Mid-Beacon Hill': 'Mid-Beacon Hill',
        'Seward Park': 'Seward Park',
        'Brighton': 'Brighton',
        'Rainier View': 'Rainier View',
        'Rainier Beach': 'Rainier View',
        'Dunlap': 'Rainier View',
        'South Park': 'West Seattle',
        'West Seattle': 'West Seattle',
        'High Point': 'West Seattle',
        'Junction': 'West Seattle',
        'South Delridge': 'West Seattle',
        'North Admiral': 'West Seattle',
        'Maple Valley': 'Maple Valley',
        'Kirkland': 'Kirkland',
        'North Rose Hill': 'Kirkland',
        'South Rose Hill': 'Kirkland',
        'Inglewood-Finn Hill': 'Kirkland',
        'Kingsgate': 'Kirkland',
        'South Juanita': 'Kirkland',
        'Bridle Trails': 'Kirkland',
        'Totem Lake': 'Kirkland',
        'North Juanita': 'Kirkland',
                         'Market': 'Kirkland',
                      'Lakeview': 'Kirkland',
        'Highlands': 'Kirkland',
        'Central Houghton': 'Kirkland',
                     'Everest': 'Kirkland',
        'Willow - Rose Hill': 'Kirkland',
        'Norkirk': 'Kirkland',
        'Lakeview': 'Kirkland',
        'Moss Bay': 'Kirkland',
        'Grass Lawn': 'Kirkland',
        'Snohomish': 'Snohomish',
        'Silver Firs': 'Snohomish',
        'Lake Bosworth': 'Snohomish',
        'Bothell': 'Snohomish',
        'Monroe': 'Snohomish',
        'Arbors at Rock Creek': 'Maple Valley',
        'Bonney Lake': 'Bonney Lake',
        'Lake Tapps': 'Bonney Lake',
        'Sumner': 'Sumner',
        'Enumclaw': 'Enumclaw',
        'Buckley': 'Buckley',
        'South Prairie': 'Buckley',
        'Everett': 'Everett',

    }

    HOMETYPES = [SW.CONDO, SW.TOWNHOUSE, SW.SINGLE_FAMILY, SW.APARTMENT]
    # NEIGHBORHOOD2 = ['Ballard', 'Fremont', 'Crown Hill', 'Green Wood', 'Phinney Ridge', 'Wallingford', 'North Beach',
    #                  'Blue Ridge', 'Whittier Heights', 'Loyal Heights', 'Sunset Hill', 'Magnolia', 'Queen Anne']


import os


class GuessGameConfig(object):
    # How often new homes are picked: 'daily' or 'weekly' (weekly picks on GAME_WEEKDAY, 0=Monday)
    GAME_FREQUENCY = os.getenv('GAME_FREQUENCY', 'daily')
    GAME_WEEKDAY = int(os.getenv('GAME_WEEKDAY', '0'))
    MIN_DAYS_PENDING = int(os.getenv('GAME_MIN_DAYS_PENDING', '14'))
    MAX_DAYS_PENDING = int(os.getenv('GAME_MAX_DAYS_PENDING', '120'))
    PICKS_PER_RUN = int(os.getenv('GAME_PICKS_PER_RUN', '2'))
    MIN_PHOTOS = 5
    # Zillow API budget per run
    MAX_PICK_LOOKUPS_PER_RUN = int(os.getenv('GAME_MAX_PICK_LOOKUPS', '8'))
    MAX_STATUS_CHECKS_PER_RUN = int(os.getenv('GAME_MAX_STATUS_CHECKS', '60'))
    EXPIRE_AFTER_DAYS = 90
    PACKAGE_RECIPIENT = os.getenv('GAME_PACKAGE_RECIPIENT', 'waichak.luk@gmail.com')
    ADMIN_EMAIL = os.getenv('GAME_ADMIN_EMAIL', 'waichak.luk@gmail.com')
    # Email every entrant the result when a round is scored
    NOTIFY_ENTRANTS = os.getenv('GAME_NOTIFY_ENTRANTS', 'false').lower() == 'true'
    BASE_URL = os.getenv('GAME_BASE_URL', 'https://www.drillbreaker29.com')
    # Public game page players are sent to; {id} is the round id.
    # Switch to e.g. https://www.wayber.ai/game/{id} once that page is live.
    GAME_PAGE_URL = os.getenv('GAME_PAGE_URL', BASE_URL.rstrip('/') + '/game/{id}')
    # Sites allowed to call the /api/game endpoints from the browser
    ALLOWED_ORIGINS = [o.strip() for o in
                       os.getenv('GAME_ALLOWED_ORIGINS', 'https://www.wayber.ai,https://wayber.ai').split(',') if o.strip()]
    # Protects /game/admin and the scheduled-task endpoint; both are locked if unset
    ADMIN_PASSWORD = os.getenv('GAME_ADMIN_PASSWORD')
