# import MySQLdb
import sshtunnel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
DB_USER = 'FatPanda1985'
DB_PASSWORD = 'wayber_housing'
DB_NAME = 'FatPanda1985$housingdata'
Base = declarative_base()
import pandas as pd
# from app.DBModels.BriefListing import BriefListing

def print_and_log(message):
    log_file_path = 'logfile.txt'  # Specify your log file name here
    print(message)
    with open(log_file_path, 'a') as file:
        file.write(message + '\n')


# Usage
error_message = "This is an error message"
import os
import json
if not os.path.exists('addressjson'):
    os.mkdir('addressjson')
print_and_log(datetime.now().__str__())

file_path = 'app/MapTools/WSDOT_-_City_Limits.geojson'
with open(file_path, 'r') as f:
    WA_geojson_data = json.load(f)
WA_geojson_features = WA_geojson_data['features']


with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
    remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
) as tunnel:

    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}')
    Base.metadata.create_all(engine)  # Create tables if they don't exist

    for feature in WA_geojson_features:
        print(feature['properties']['CityName'])
        cityname = feature['properties']['CityName']
        # print(washingtoncitiescontroller.getCity(cityname))
    try:
        df = pd.read_sql("SELECT * FROM Customer", con=engine)

        print(df)
        # Session = sessionmaker(bind=engine)
        # session = Session()
        #
        # # Define the batch size
        # batch_size = 100
        # entries_to_update = []
        #
        # # Query the total number of entries
        # query = session.query(BriefListing).filter(BriefListing.price > 500000)
        # print(query.all())
        # df = pd.read_sql(query.statement, session.bind)
        # csv_file_name = 'newbuild2016.csv'
        # df.to_csv(csv_file_name, index=False)
        # print_and_log(f"Data written to {csv_file_name}")

    except Exception as e:
        print_and_log(f"Error: {e}")
    finally:
        # session.close()
        tunnel.stop()

