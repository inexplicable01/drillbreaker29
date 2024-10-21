import MySQLdb
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
from app.DBModels.BriefListing import BriefListing

def print_and_log(message):
    log_file_path = 'logfile.txt'  # Specify your log file name here
    print(message)
    with open(log_file_path, 'a') as file:
        file.write(message + '\n')


# Usage
error_message = "This is an error message"
import os

if not os.path.exists('addressjson'):
    os.mkdir('addressjson')
print_and_log(datetime.now().__str__())




with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
    remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
) as tunnel:

    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}')
    Base.metadata.create_all(engine)  # Create tables if they don't exist
    # Do stuff


    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # Define the batch size
        batch_size = 100
        entries_to_update = []

        # Query the total number of entries
        query = session.query(BriefListing).filter(BriefListing.price > 500000)
        df = pd.read_sql(query.statement, session.bind)
        csv_file_name = 'newbuild2016.csv'
        df.to_csv(csv_file_name, index=False)
        print_and_log(f"Data written to {csv_file_name}")

    except MySQLdb.Error as e:
        print_and_log(f"Error: {e}")
    finally:
        session.close()
        tunnel.stop()

