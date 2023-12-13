def find_construction_year(data, path=None, keys_of_interest=None):
    if keys_of_interest is None:
        keys_of_interest = {'year_built', 'construction_date', 'built_year', 'date_built'}
    if path is None:
        path = []  # Initialize the path

    if isinstance(data, dict):  # If the item is a dictionary, iterate over its keys
        for key, value in data.items():
            new_path = path + [key]  # Append the current key to the path
            # If the key looks like one that would indicate a construction date, print it and the path
            if any(k in key.lower() for k in keys_of_interest):
                print(f"Found {key}: {value}")
                print(f"To access it, use the path: {' -> '.join(new_path)}")
            # If the value is another dictionary, recurse into it
            elif isinstance(value, dict):
                find_construction_year(value, new_path, keys_of_interest)
            # If the value is a list, iterate over it as it may contain dictionaries
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    find_construction_year(item, new_path + [str(index)], keys_of_interest)

# Example usage with a nested dictionary
property_info = {
    'address': '123 Fake Street',
    'property_details': {
        'year_built': 1990,
        'owner': 'John Doe',
        'renovation_details': {
            'last_renovated': 2010,
            'renovation_cost': 50000
        }
    },
    'construction_info': {
        'construction_date': '1989-07-23',
        'builders': 'XYZ Constructions'
    }
}

find_construction_year(property_info)



