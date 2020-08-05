import sqlite3
import json
from datetime import datetime

timeframe = '2015-05'

sql_transaction = []
start_row = 0
cleanup = 1000000

# connect with db
connection = sqlite3.connect('{}.db'.format(timeframe))

cursor = connection.cursor();


# create table
def create_table():
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS parent_reply(parent_id TEXT PRIMARY KEY, comment_id TEXT UNIQUE, parent TEXT, comment TEXT, subreddit TEXT, unix INT, score INT)")
    # """CREATE TABLE IF NOT EXISTS parent_reply(parent_id TEXT PRIMARY KEY, comment_id TEXT UNIQUE, parent TEXT, coment TEXT, subreddit TEXT, unix INT, score INT)""")


def format_data(data):
    data = data.replace('\n', ' newlinechar ').replace('\r', ' newlinechar ').replace('"', "'")
    # data = data.replace("\n", "new_line").replace("\r", "new_line").replace('"', "'")
    return data


def find_parent(parentid):
    try:
        sql = "SELECT comment FROM parent_reply WHERE comment_id = '{}' LIMIT 1".format(parentid)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result != None:
            return result[0]
        else:
            return False
    except Exception as exception:
        print("In find_parent", exception)
        return False


def acceptOrNot(data):
    if len(data.split(' ')) > 1000 or len(data) < 1:
        return False
    elif len(data) > 32000:
        return False
    elif data == '[deleted]':
        return False
    elif data == '[removed]':
        return False
    else:
        return True


def find_existing_score(parentid):
    try:
        sql = "SELECT score FROM parent_reply WHERE parent_id = '{}' LIMIT 1".format(parentid)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result != None:
            return result[0]
        else:
            return False
    except Exception as exception:
        print("In find_existing_score", exception)
        return False


def transaction_bldr(sql):
    global sql_transaction
    sql_transaction.append(sql)
    if len(sql_transaction) > 1000:
        cursor.execute('BEGIN TRANSACTION')
        for statement in sql_transaction:
            try:
                cursor.execute(statement)
            except:
                pass
        connection.commit()
        sql_transaction = []


def sql_insert_replace_comment(commentid, parentid, parent, comment, subreddit, time, score):
    try:
        sql = """UPDATE parent_reply SET parent_id = ?, comment_id = ?, parent = ?, comment = ?, subreddit = ?, unix = ?, score = ? WHERE parent_id =?;""".format(
            parentid, commentid, parent, comment, subreddit, int(time), score, parentid)
        transaction_bldr(sql)
    except Exception as exception:
        print('In sql_insert_replace_comment', str(exception))


def sql_insert_has_parent(commentid, parentid, parent, comment, subreddit, time, score):
    try:
        sql = """INSERT INTO parent_reply (parent_id, comment_id, parent, comment, subreddit, unix, score) VALUES ("{}","{}","{}","{}","{}",{},{});""".format(
            parentid, commentid, parent, comment, subreddit, int(time), score)
        transaction_bldr(sql)
    except Exception as exception:
        print('In sql_insert_has_parent', str(exception))


def sql_insert_hasnt_parent(commentid, parentid, comment, subreddit, time, score):
    try:
        sql = """INSERT INTO parent_reply (parent_id, comment_id, comment, subreddit, unix, score) VALUES ("{}","{}","{}","{}",{},{});""".format(
            parentid, commentid, comment, subreddit, int(time), score)
        transaction_bldr(sql)
    except Exception as exception:
        print('In sql_insert_no_parent', str(exception))


if __name__ == "__main__":
    create_table()
    row_counter = 0  # how many rows in the db
    paired_rows = 0  # how many parent and child pairs have

    with open("RC_2015-05".format(timeframe), buffering=1000) as f:
        for row in f:
            # print(row)
            row_counter += 1

            if row_counter > start_row:
                try:
                    row = json.loads(row)
                    parent_id = row['parent_id'].split('_')[1]
                    body = format_data(row['body'])
                    created_utc = row['created_utc']
                    score = row['score']

                    comment_id = row['id']

                    subreddit = row['subreddit']
                    parent_data = find_parent(parent_id)

                    existing_comment_score = find_existing_score(parent_id)
                    if existing_comment_score:
                        if score > existing_comment_score:
                            if acceptOrNot(body):
                                sql_insert_replace_comment(comment_id, parent_id, parent_data, body, subreddit,
                                                           created_utc, score)

                    else:
                        if acceptOrNot(body):
                            if parent_data:
                                if score >= 2:
                                    sql_insert_has_parent(comment_id, parent_id, parent_data, body, subreddit,
                                                          created_utc, score)
                                    paired_rows += 1
                            else:
                                sql_insert_hasnt_parent(comment_id, parent_id, body, subreddit, created_utc, score)
                except Exception as e:
                    print(str(e))

            if row_counter % 100000 == 0:
                print('Total Rows Read: {}, Paired Rows: {}, Time: {}'.format(row_counter, paired_rows,
                                                                              str(datetime.now())))
            if row_counter > start_row:
                if row_counter % cleanup == 0:
                    print("Cleanin up!")
                    sql = "DELETE FROM parent_reply WHERE parent IS NULL"
                    cursor.execute(sql)
                    connection.commit()
                    cursor.execute("VACUUM")
                    connection.commit()

