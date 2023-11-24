import MySQLdb
import sshtunnel
import pandas as pd
from pathlib import Path




csv_file_path = 'bellevueaddresstax.csv'  # Replace with the path to your Excel file
table_name = 'BellevueAddressFromTax'  # Replace with your desired table name
sheet_name = 'tax'  # Replace with your Excel sheet name

if not Path(csv_file_path).is_file():
    raise FileNotFoundError(f"The file {csv_file_path} does not exist.")

# Read the Excel file into a pandas DataFrame
# df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
df = pd.read_csv(csv_file_path)


sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='FatPanda1985', ssh_password='Lowlevelpw01!',
    remote_bind_address=('FatPanda1985.mysql.pythonanywhere-services.com', 3306)
) as tunnel:
    connection = MySQLdb.connect(
        user='FatPanda1985',
        passwd='wayber_housing',
        host='127.0.0.1', port=tunnel.local_bind_port,
        db='FatPanda1985$housingdata',
    )
    # Do stuff
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"MySQL server version: {version}")
            # load_excel_to_mysql(excel_file_path, table_name, connection, sheet_name)
            df.to_sql(table_name, connection, if_exists='replace', index=False)
    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        connection.close()