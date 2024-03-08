

def BodyNewListing(sorted_houses):
    html_content = '''
    <table border="1">
        <tr>
            <th>Link</th>
            <th>Price</th>
            <th>Beds</th>
            <th>Bath</th>
            <th>Square ft</th>
            <th>Days on Market</th>
            <th>Agent Name</th>
            <th>Agent Number</th>
            <th>Neighbourhood</th>
        </tr>'''

    for house in sorted_houses:
        row = f'''
        <tr>
            <td><a href='https://www.zillow.com{house['hdpUrl']}' target='_blank'>House Link</a></td>
            <td>{house['price']}</td>
            <td>{house['bedrooms']}</td>
            <td>{house['bathrooms']}</td>
            <td>{house['livingArea']}</td>
            <td>{house['daysOnZillow']}</td>
            <td>{house['attributionInfo']['agentName']}</td>
            <td>{house['attributionInfo']['agentPhoneNumber']}</td>
            <td>{house.get('neighborhoodRegion', {}).get('name', 'N/A')}</td>
        </tr>
        '''
        html_content += row
    html_content += '</table>'
    return html_content