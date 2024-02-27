import MySQLdb
import sshtunnel
from app.ZillowAPI.ZillowAddress import ZillowAddress
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.ZillowAPI.ZillowHandler import loadPropertyDataFromAddress
from datetime import datetime
sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
DB_USER = 'FatPanda1985'
DB_PASSWORD = 'wayber_housing'
DB_NAME = 'FatPanda1985$housingdata'
Base = declarative_base()
from app.DBModels.BellevueTaxAddress import BellevueTaxAddress


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

        # Define the batch size
        batch_size = 100
        entries_to_update = []

        # Query the total number of entries
        # query = session.query(BellevueTaxAddress).filter(BellevueTaxAddress.year_built > 2016)
        # df = pd.read_sql(query.statement, session.bind)
        # csv_file_name = 'newbuild2016.csv'
        # df.to_csv(csv_file_name, index=False)
        # print_and_log(f"Data written to {csv_file_name}")
        # count = session.query(BellevueTaxAddress).filter(BellevueTaxAddress.postalcityname=="BELLEVUE").scalar()
        # # Process in batches
        entries = session.query(BellevueTaxAddress).filter(BellevueTaxAddress.postalcityname=="BELLEVUE").all()
        # bellevue_rows = query.all()
        # for offset in range(0, total_entries, batch_size):
        #     entries = session.query(BellevueTaxAddress).limit(batch_size).offset(offset).all()

        for bellevueaddr in entries:
            fileaddress = bellevueaddr.addr_full +'  ' + bellevueaddr.postalcityname
            try:
                # if bellevueaddr.living_area is None and "R" in bellevueaddr.sitetype and bellevueaddr.postalcityname=='BELLEVUE':
                if os.path.exists(os.path.join('addressjson',fileaddress+'.txt')):
                    # with open(os.path.join('addressjson',fileaddress+'.txt'), 'r') as file:
                    #     # Read the content of the file
                    #     text_content = file.read()
                    propertydata = loadPropertyDataFromAddress(fileaddress)
                    zaddress = ZillowAddress.LoadZFD(propertydata)
                else:
                    addressStr=bellevueaddr.addr_full +'  ' + bellevueaddr.postalcityname + ' ' + str(bellevueaddr.zip5)
                    propertydata = loadPropertyDataFromAddress(addressStr)
                    json_string = json.dumps(propertydata, indent=4)
                    with open(os.path.join('addressjson',fileaddress+'.txt'), 'w') as f:
                        f.write(json_string)
                    zaddress = ZillowAddress.OpenAddresstxt(fileaddress)
                if zaddress.resoFacts['hasWaterfrontView']:
                    # if propertydata['zestimate'] is None or propertydata['yearBuilt'] is None:
                    #     print_and_log(bellevueaddr.addr_full + '  is residential but doesnt have zestimate or year built')
                    #     continue
                    print_and_log(bellevueaddr.addr_full + '  ' + bellevueaddr.postalcityname)
                    entries_to_update.append({
                        'id': bellevueaddr.id,  # assuming there's an 'id' primary key
                        'haswaterfrontview': zaddress.resoFacts['hasWaterfrontView']})
                else:
                    # if 'error' in propertydata.keys():
                    #     print_and_log(bellevueaddr.addr_full + '  error:' + propertydata['error'])
                    # else:
                    print_and_log(bellevueaddr.addr_full + '  has no water front ')
            except Exception as e:
                print_and_log(f"{bellevueaddr.addr_full} +   error!!! {str(e)}")


        #     # If there are updates to be made, do them in a bulk operation
            if len(entries_to_update)>100:
                try:
                    # print_and_log(str(batch))
                    print_and_log('updating')
                    session.bulk_update_mappings(BellevueTaxAddress, entries_to_update)
                    print_and_log('commiting')
                    session.commit()
                    entries_to_update = []  # Clear the list for the next batch
                except Exception as e:
                    print_and_log(f"Error during bulk update: {str(e)}")
                    session.rollback()

        # def AllListings():
        #     results = Listing.query.all()
        #     verifiedresults = []
        #     for index, result in enumerate(results):
        #         if result is None:
        #             # print_and_log(f"None found at index {index}")
        #             continue
        #         else:
        #             # Assuming 'Listing' has an 'id' attribute
        #             # print_and_log(f"Listing ID: {result.id}")
        #             verifiedresults.append(result)
        #
        #     return results

    except MySQLdb.Error as e:
        print_and_log(f"Error: {e}")
    finally:
        session.close()
        tunnel.stop()


