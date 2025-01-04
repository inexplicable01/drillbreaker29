SOLD="recentlySold"

class SW(object):
    TOWNHOUSE = 'TOWNHOUSE'
    SINGLE_FAMILY = 'SINGLE_FAMILY'
    CONDO = 'CONDO'
    APARTMENT='APARTMENT'


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
