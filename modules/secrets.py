import mysql.connector
from mysql.connector import Error

sql_host = 'localhost'
sql_database = 'bgecosystem2'
sql_user = 'root'
sql_password = ''


def serverconnect():
    try:
        conn = mysql.connector.connect(
            host=sql_host, database=sql_database, user=sql_user, password=sql_password)
        if conn.is_connected():
            return conn
        else:
            return None
    except Error as e:
        return None
