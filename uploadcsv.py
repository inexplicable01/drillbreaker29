import MySQLdb
import sshtunnel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime
import os

# Constants
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
DB_USER = 'FatPanda1985'
DB_PASSWORD = 'wayber_housing'
DB_NAME = 'FatPanda1985$housingdata'
Base = declarative_base()
log_file_path = 'logfile.txt'
csv_file_path = 'C:/Users/waich/Box Sync/Wayber/Website/washington_cities.csv'  # Path to the CSV file

# Logging function
def print_and_log(message):
    print(message)
    with open(log_file_path, 'a') as file:
        file.write(message + '\n')

# Ensure necessary directories exist
if not os.path.exists('addressjson'):
    os.mkdir('addressjson')

# Log the current time
print_and_log(datetime.now().__str__())

# Set up the SSH tunnel and database connection
with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
    remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
) as tunnel:

    engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{tunnel.local_bind_port}/{DB_NAME}')
    Base.metadata.create_all(engine)  # Create tables if they don't exist

    try:
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path)

        # Define the table name where you want to upload the data
        table_name = 'WashingtonCities'

        # Upload the DataFrame to the database
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)

        print_and_log(f"Data from {csv_file_path} has been uploaded to the table {table_name}")

    except MySQLdb.Error as e:
        print_and_log(f"Error: {e}")
    finally:
        session.close()
        tunnel.stop()
