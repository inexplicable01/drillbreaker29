import MySQLdb
import sshtunnel
import pandas as pd
from pathlib import Path
import numpy as np
from sqlalchemy import create_engine, Column, Integer, Float, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

csv_file_path = 'bellevueaddresstax.csv'  # Replace with the path to your Excel file
table_name = 'BellevueAddressFromTax'  # Replace with your desired table name
sheet_name = 'tax'  # Replace with your Excel sheet name

from BellevueTaxAddress import BellevueTaxAddress
Base = declarative_base()
if not Path(csv_file_path).is_file():
    raise FileNotFoundError(f"The file {csv_file_path} does not exist.")

# Read the Excel file into a pandas DataFrame
# df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
columns_to_keep = ['SITEID','ADDR_FULL', 'COMMENTS', 'ZIP5','SITETYPE','POSTALCTYNAME','POINT_X', 'POINT_Y', 'latitude','longitude','Shape_Length', 'Shape_Area']
dtype_dict = {
# 'ADDR_FULL': str, 'COMMENTS': str, 'SITETYPE': str, 'SITEID': str, 'ADDR_HN': str, 'ADDR_PD': str,
#        'ADDR_PT': str, 'ADDR_SN': str, 'ADDR_ST': str, 'ADDR_SD': str, 'ADDR_NUM': str, 'FULLNAME': str,
#        'ZIP5': int, 'POSTALCTYNAME': str, 'latitude':float, 'longitude':float, 'POINT_X':float, 'POINT_Y':float,
#        'COUNTY': str, 'KROLL': str ,'first': str, 'KCTP_CITY': str, 'KCTP_STATE': str, 'PLSS': str,
#        'PROP_NAME': str,
#        'Shape_Length':float, 'Shape_Area':float,
    8: str,   # or float, int, etc., depending on what you expect
    17: str,  # or float, int, etc., depending on what you expect
    25: str,  # or float, int, etc., depending on what you expect
    'ZIP5': 'Int64'   # or float, int, etc., depending on what you expect
}
df = pd.read_csv(csv_file_path, dtype=dtype_dict,usecols=columns_to_keep)
df = df.replace({np.nan: None})
# for index, row in df.head(100).iterrows():
#     print(f"Row {index}:")
#     print(row['ADDR_FULL'], row['POSTALCTYNAME'], row['ZIP5'])
#     print()  # Prints a newline for readability

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
DB_USER = 'FatPanda1985'
DB_PASSWORD = 'wayber_housing'
DB_NAME = 'FatPanda1985$housingdata'
with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
    remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
) as tunnel:
    # connection = MySQLdb.connect(
    #     user='FatPanda1985',
    #     passwd='wayber_housing',
    #     host='127.0.0.1', port=tunnel.local_bind_port,
    #     db='FatPanda1985$housingdata',
    # )
    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}')
    Base.metadata.create_all(engine)  # Create tables if they don't exist
    # Do stuff
    try:
        Session = sessionmaker(bind=engine)
        session = Session()


        first_hundred_entries = session.query(BellevueTaxAddress).all()

        # for bellevueaddr in first_hundred_entries:
        #     matching_row = df[df['ADDR_FULL'] == bellevueaddr.addr_full]
        #     # print(matching_row)
        #     print(matching_row['SITETYPE'].iloc[0])
        #     bellevueaddr.sitetype=matching_row['SITETYPE'].iloc[0]
        # session.commit()

        # Step 1: Create a mapping from your DataFrame
        addr_to_sitetype = dict(zip(df['ADDR_FULL'], df['SITETYPE']))

        # Step 2: Prepare a list of dictionaries for the update
        updates = []
        for bellevueaddr in first_hundred_entries:
            if bellevueaddr.addr_full in addr_to_sitetype:
                print(bellevueaddr.addr_full +'   ' + addr_to_sitetype[bellevueaddr.addr_full])
                updates.append({
                    'id': bellevueaddr.id,  # Assuming there's an 'id' primary key column
                    'sitetype': addr_to_sitetype[bellevueaddr.addr_full]
                })

        # Perform the bulk update
        if updates:  # only if there are updates to be made
            session.bulk_update_mappings(BellevueTaxAddress, updates)
            print('committing')
            session.commit()

        # for index, row in df[30000:-1].iterrows():
        #     existing_listing = session.query(BellevueTaxAddress).filter_by(addr_full=row['ADDR_FULL']).first()
        #     if existing_listing is None:
        #         new_bellevuetaxaddress = BellevueTaxAddress(
        #             addr_full=row['ADDR_FULL'],
        #             comments=row['COMMENTS'],
        #             sitetype=row['SITETYPE'],
        #             zip5=row['ZIP5'],
        #             postalcityname=row['POSTALCTYNAME'],
        #             latitude=row['latitude'],
        #             longitude=row['longitude'],
        #             point_x=row['POINT_X'],
        #             point_y=row['POINT_Y'],
        #             shape_length=row['Shape_Length'],
        #             shape_area=row['Shape_Area']
        #         )
        #         print(new_bellevuetaxaddress)
        #         session.add(new_bellevuetaxaddress)

        # session.commit()

        # Commit all the new records to the database

            # load_excel_to_mysql(excel_file_path, table_name, connection, sheet_name)
            # df.to_sql(table_name, connection, if_exists='replace', index=False)
    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        session.close()
        tunnel.stop()

