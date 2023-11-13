import MySQLdb
import sshtunnel

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
    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        connection.close()