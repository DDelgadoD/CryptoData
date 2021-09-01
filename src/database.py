import mysql.connector

import secrets


def connect():
    return mysql.connector.connect(
        host=secrets.host,
        user=secrets.user,
        password=secrets.password
    )


# Connect to Local Database
my_db = connect()

# Creating a cursor to make the sql callings
cursor = my_db.cursor()
