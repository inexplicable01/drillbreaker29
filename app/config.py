
class SW(object):
    TOWNHOUSE='TOWNHOUSE'
    SINGLE_FAMILY='SINGLE_FAMILY'
    CONDO='CONDO'

class Config(object):
    NEIGHBORHOODS =  ['Ballard','Fremont','Crown Hill','Green Wood','Phinney Ridge','Wallingford','North Beach',
                    'Blue Ridge','Whittier Heights','Loyal Heights','Sunset Hill','Magnolia','Queen Anne']
    WRONGNEIGHBORHOODS =  ['Maple Leaf','South Lake Union','Bryant','Laurelhurst',
                           'Madison Park','Madison','Capitol Hill','Roosevelt','Eastlake']


    HOMETYPES=[SW.CONDO,SW.TOWNHOUSE,SW.SINGLE_FAMILY]
    # NEIGHBORHOOD2 = ['Ballard', 'Fremont', 'Crown Hill', 'Green Wood', 'Phinney Ridge', 'Wallingford', 'North Beach',
    #                  'Blue Ridge', 'Whittier Heights', 'Loyal Heights', 'Sunset Hill', 'Magnolia', 'Queen Anne']