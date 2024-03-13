import mariadb
import os
import pytz
import re
import sys

from datetime import datetime, date, time


DB_HOST = "192.168.1.2"
DB_PORT = 3306
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = "chatlogs_test"
PATH_TO_LOGS = "./sample/"


def connect_to_db():
    try:
        return mariadb.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
    except mariadb.Error as err:
        print(f"Error while connecting to database: {err}")
        sys.exit(1)


def write_message_to_db(pseudo: str, message: str, channel: str, timestamp):
    try:
        # TODO: not initiate a connection each time we write a message
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO message (pseudo, message, channel, timestamp) VALUES (?, ?, ?, ?)",
            (pseudo, message, channel, timestamp)
        )
        conn.commit()
        conn.close()
    except mariadb.Error as err:
        print(f"Error while adding message to database: {err}")


def parse_line(line: str):
    try:
        timestamp = re.search(r'\[(.*?)\]', line).group(1)
        pseudo = re.search(r'] (.*?):', line).group(1)
        message = re.search(r': (.*?)$', line).group(1)
    except (TypeError, AttributeError) as err:
        return None, None, None
    return timestamp.split(":"), pseudo, message

def parse_file(dirpath: str, file: str):
    path = os.path.join(dirpath, file)
    channel = file.split('-')[0]
    date_us = file.replace(f"{channel}-", "")[:-4].split('-')

    with open(path, "r") as f:
        for line in f.readlines():
            if line[0] == "#":
                continue
            
            timestamp, pseudo, message = parse_line(line)
            
            if None in (timestamp, pseudo, message):
                continue
            
            date_object = datetime.combine(
                date(int(date_us[0]), int(date_us[1]), int(date_us[2])),
                time(int(timestamp[0]), int(timestamp[1]), int(timestamp[2]), tzinfo=pytz.timezone("Europe/Paris"))
            )

            write_message_to_db(
                pseudo=pseudo,
                message=message,
                channel=channel,
                timestamp=date_object
            )



def parse_and_write_to_db():
    for dirpath, _, files in os.walk(PATH_TO_LOGS):
        for file in files:
            print(f"Processing {os.path.join(dirpath, file)} ...")
            parse_file(dirpath, file)


connect_to_db()
parse_and_write_to_db()
