import sqlite3

from src.config import *

class DatabaseManager:
    def __init__(self):
       pass

    def initialize(self):
        if not os.path.exists(DB_PATH):
            print(f"DB file '{DB_PATH}' does not exist. Creating a new one.")
            with sqlite3.Connection(DB_PATH) as connection:
                cursor = connection.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
                connection.commit()
