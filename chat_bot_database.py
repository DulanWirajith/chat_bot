import sqlite3
import json
from datetime import datetime

timeframe = '2015-05'

sql_transcation = []

connection = sqlite3.connect('{}.db'.format(timeframe))

cursor = connection.cursor();


def create_table():
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS parent_reply(parent_id TEXT PRIMARY KEY, comment_id TEXT UNIQUE, parent TEXT, coment TEXT, subreddit TEXT, unix INT, score INT)""")

if __name__=="__main__":
    create_table()
