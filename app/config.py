
class SW(object):
    TOWNHOUSE='TOWNHOUSE'
    SINGLE_FAMILY='SINGLE_FAMILY'
    CONDO='CONDO'

class Config(object):
    NEIGHBORHOODS =  ['Ballard','Fremont','Crown Hill','Green Wood','Phinney Ridge','Wallingford','North Beach',
                    'Blue Ridge','Whittier Heights','Loyal Heights','Sunset Hill','Magnolia','Queen Anne']
    WRONGNEIGHBORHOODS =  ['Maple Leaf','South Lake Union','Bryant','Laurelhurst',
                           'Madison Park','Madison','Capitol Hill','Roosevelt','Eastlake']
    SEATTLE_GAPIS_TO_NEIGH = {
        'Adams':'Ballard',
        'Ballard':'Ballard',
        'West Woodland':'Ballard',
        'Loyal Heights':'Ballard',
        'Northwest Seattle':'Phinney Ridge and Greenlake',
        'Maple Leaf':'Phinney Ridge and Greenlake',
        'North Beach/Blue Ridge':'North Beach/Blue Ridge',
        'Crown Hill':'Crown Hill',
        'Broadview':'Broadview',
        'Wallingford':'Wallingford',
        'Fremont':'Fremont',
        'Northgate':'Northgate',
        'Meadowbrook':'North Seattle',
        'North Seattle':'North Seattle',
        'Cedar Park':'North Seattle',
        'Matthews Beach':'North Seattle',
        'Northeast Seattle':'Northeast Seattle',
        'Southeast Magnolia':'Magnolia',
        'Olympic Hills':'Northeast Seattle',
        'Magnolia':'Magnolia',
        'East Queen Anne':'Queen Anne',
        'North Queen Anne':'Queen Anne',
        'Queen Anne': 'Queen Anne',
        'West Queen Anne': 'Queen Anne',
        'Westlake':'Queen Anne',
        'Uptown':'Seattle Center',
        'South Lake Union':'Seattle Center',
        'Downtown Seattle':'Seattle Center',
        'Yesler Terrace': 'Central District',
        'Leschi':'Central District',
        'Minor': 'Central District',
        'Central District': 'Central District',
        'Madison Park': 'Madison Park',
        'Washington Park': 'Madison Park',
        'Madison Valley': 'Madison Park',
        'Capitol Hill':'Capitol Hill',
        'Stevens':'Capitol Hill',
        'Miller Park':'Capitol Hill',
        'Eastlake':'Eastlake',
        'Greater Duwamish':'Beacon Hill',
        'Rainier Vista': 'Beacon Hill',
        'Mount Baker':'Rainier Valley',
        'Rainier Valley':'Rainier Valley',
        'Mid-Beacon Hill':'Mid-Beacon Hill',
        'Seward Park':'Seward Park',
        'Brighton':'Brighton',
        'Rainier View':'Rainier View',
        'Rainier Beach': 'Rainier View',
        'Dunlap': 'Rainier View',
        'South Park':'West Seattle',
        'West Seattle': 'West Seattle',
        'High Point': 'West Seattle',
        'Junction':'West Seattle',
        'South Delridge': 'West Seattle',
        'North Admiral': 'West Seattle',


















    }

    HOMETYPES=[SW.CONDO,SW.TOWNHOUSE,SW.SINGLE_FAMILY]
    # NEIGHBORHOOD2 = ['Ballard', 'Fremont', 'Crown Hill', 'Green Wood', 'Phinney Ridge', 'Wallingford', 'North Beach',
    #                  'Blue Ridge', 'Whittier Heights', 'Loyal Heights', 'Sunset Hill', 'Magnolia', 'Queen Anne']