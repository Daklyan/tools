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
PATH_TO_LOGS = "/mnt/c/Users/bolos/AppData/Roaming/Chatterino2/Logs/Twitch/Channels/"

class Database():
    def __init__(self):
        try:
            self.connection = mariadb.connect(
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME
            )
            self.cursor = self.connection.cursor()
        except mariadb.Error as err:
            print(f"Error while connecting to database: {err}")
            sys.exit(1)

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor

    def close_connection(self):
        self.connection.close()


class Parser():
    def __init__(self, database: Database):
        self.db = database
        self.conn = self.db.get_connection()
        self.cur = self.db.get_cursor()

    def check_if_file_is_done(self, filename: str) -> bool:
        try:
            self.cur.execute(
                "SELECT id FROM done_file WHERE file=?",
                (filename,)
            )
            if self.cur.fetchone():
                return True
        except mariadb.Error as err:
            print(f"Error fetching file in done_file in database: {err}")
        return False

    def write_message_to_db(self, pseudo: str, message: str, channel: str, timestamp):
        try:
            self.cur.execute(
                "INSERT INTO message (pseudo, message, channel, timestamp) VALUES (?, ?, ?, ?)",
                (pseudo, message, channel, timestamp)
            )
            self.conn.commit()
        except mariadb.Error as err:
            print(f"Error while adding message to database: {err}")

    def write_file_to_done(self, channel: str, filename: str):
        try:
            self.cur.execute(
                "INSERT INTO done_file (channel, file) VALUES (?, ?)",
                (channel, filename)
            )
            self.conn.commit()
        except mariadb.Error as err:
            print(f"Error while adding file to done in database: {err}")

    def parse_line(self, line: str):
        try:
            timestamp = re.search(r'\[(.*?)\]', line).group(1)
            pseudo = re.search(r'] (.*?):', line).group(1)
            message = re.search(r': (.*?)$', line).group(1)
        except (TypeError, AttributeError) as err:
            return None, None, None
        return timestamp.split(":"), pseudo, message

    def parse_file(self, dirpath: str, file: str):
        path = os.path.join(dirpath, file)
        channel = file.split('-')[0]
        date_us = file.replace(f"{channel}-", "")[:-4].split('-')

        if self.check_if_file_is_done(filename=file):
            print(f"File {file} already exported, skipping!")
            return

        with open(path, "r") as f:
            for line in f.readlines():
                if line[0] == "#":
                    continue
                
                timestamp, pseudo, message = self.parse_line(line)
                
                if None in (timestamp, pseudo, message):
                    continue
                
                date_object = datetime.combine(
                    date(int(date_us[0]), int(date_us[1]), int(date_us[2])),
                    time(int(timestamp[0]), int(timestamp[1]), int(timestamp[2]), tzinfo=pytz.timezone("Europe/Paris"))
                )

                self.write_message_to_db(
                    pseudo=pseudo,
                    message=message,
                    channel=channel,
                    timestamp=date_object
                )

            self.write_file_to_done(channel=channel, filename=file)

    def parse_and_write_to_db(self):
        for dirpath, _, files in os.walk(PATH_TO_LOGS):
            for file in files:
                print(f"Processing {os.path.join(dirpath, file)} ...")
                self.parse_file(dirpath, file)


database = Database()
parser = Parser(database)

parser.parse_and_write_to_db()
database.close_connection()
