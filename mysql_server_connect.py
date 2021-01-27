import mysql.connector
from mysql.connector import Error


def create_connection(mysql_server, user_name, user_password, daatabase_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = mysql_server,
            user = user_name,
            passwd = user_password,
            database = daatabase_name,
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")


def execute_query(connection, query): # для вставки записей
     cursor = connection.cursor()
     try:
         cursor.execute(query)
         connection.commit()
         print("Query executed successfully") # Запрос выполнен успешно
     except Error as e:
         print(f"The error '{e}' occurred")
