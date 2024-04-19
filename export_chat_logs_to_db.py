import logging
import mariadb
import os
import pytz
import re
import sys
import time as timer

from datetime import datetime, date, time


DB_HOST = "192.168.1.2"
DB_PORT = 3306
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = "chatlogs"
PATH_TO_LOGS = "/mnt/c/Users/bolos/AppData/Roaming/Chatterino2/Logs/Twitch/Channels/"
LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s] - %(asctime)s %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S",
    handlers=[logging.FileHandler("export.log"), logging.StreamHandler()],
    encoding="utf-8",
    level=logging.INFO,
)


class Database:
    def __init__(self, db_user: str, db_pass: str, host: str, port: int, database: str):
        try:
            self.connection = mariadb.connect(
                user=db_user, password=db_pass, host=host, port=port, database=database
            )
            self.cursor = self.connection.cursor()
        except mariadb.Error as err:
            LOGGER.error(f"Error while connecting to database: {err}")
            sys.exit(1)

    def get_connection(self):
        return self.connection

    def get_cursor(self):
        return self.cursor

    def close_connection(self):
        self.connection.close()


class Parser:
    def __init__(self, database: Database):
        self.db = database
        self.conn = self.db.get_connection()
        self.cur = self.db.get_cursor()

    def check_if_file_is_done(self, filename: str) -> bool:
        """Checks in database if file as already been exported

        Args:
            filename (str): Name of the file to check

        Returns:
            bool: Returns True if already done, if not returns False
        """
        try:
            self.cur.execute("SELECT id FROM done_file WHERE file=?", (filename,))
            if self.cur.fetchone():
                return True
        except mariadb.Error as err:
            LOGGER.error(f"Error fetching file in done_file in database: {err}")
        return False

    def write_many_messages_to_db(self, list_of_values: list):
        """Write logged message to database

        Args:
            list_of_values (list): List of tuples with needed parameters
        """
        if not list_of_values:
            return
        try:
            self.cur.executemany(
                "INSERT INTO message (pseudo, message, channel, timestamp) VALUES (?, ?, ?, ?)",
                list_of_values,
            )
            self.conn.commit()
        except mariadb.Error as err:
            LOGGER.error(f"Error while adding messages to database: {err}")

    def write_file_to_done(self, channel: str, filename: str):
        """Append file as done to the database

        Args:
            channel (str): Name of the twitch channel
            filename (str): File done exporting
        """
        try:
            self.cur.execute(
                "INSERT INTO done_file (channel, file) VALUES (?, ?)",
                (channel, filename),
            )
            self.conn.commit()
        except mariadb.Error as err:
            LOGGER.error(f"Error while adding file to done in database: {err}")

    def parse_line(self, line: str):
        """Parse a line to get the timestamp, pseudo and message out of it

        Args:
            line (str): Line of a chatterino log

        Returns:
            (str, str, str) | (None, None, None): Parsed values or None if it fails to
        """
        try:
            timestamp = re.search(r"\[(.*?)\]", line).group(1)
            pseudo = re.search(r"] (.*?):", line).group(1)
            message = re.search(r": (.*?)$", line).group(1)
        except (TypeError, AttributeError) as err:
            LOGGER.debug(f'Error while parsing line "{line}": {err}')
            return None, None, None
        return timestamp.split(":"), pseudo, message

    def parse_file(self, dirpath: str, file: str):
        """Go through file of a given a path, parse it and call to write in database

        Args:
            dirpath (str): Path to file
            file (str): Filename to parse
        """
        path = os.path.join(dirpath, file)
        channel = file.split("-")[0]
        date_us = file.replace(f"{channel}-", "")[:-4].split("-")
        logged_lines = []

        if date_us == datetime.today().strftime('%Y-%m-%d'):
            LOGGER.debug(f"Skipping {file} as it still could be updated today")
            return

        try:
            with open(path, "r") as f:
                for line in f.readlines():
                    timestamp, pseudo, message = self.parse_line(line)

                    if None in (timestamp, pseudo, message):
                        continue

                    date_object = datetime.combine(
                        date(int(date_us[0]), int(date_us[1]), int(date_us[2])),
                        time(
                            int(timestamp[0]),
                            int(timestamp[1]),
                            int(timestamp[2]),
                            tzinfo=pytz.timezone("Europe/Paris"),
                        ),
                    )

                    date_object.strftime("%Y-%m-%d  %H:%M:%S")
                    logged_lines.append((pseudo, message, channel, date_object))

                self.write_many_messages_to_db(list_of_values=logged_lines)

                self.write_file_to_done(channel=channel, filename=file)
        except Exception as err:
            LOGGER.debug(f"Error while parsing {file}: {err}")

    def parse_and_write_to_db(self):
        """Go through every file of a given path and starts the parsing / writing to database"""
        for dirpath, _, files in os.walk(PATH_TO_LOGS):
            for file in files:
                if self.check_if_file_is_done(filename=file):
                    LOGGER.info(f"File {file} already exported, skipping!")
                    continue
                LOGGER.info(f"Processing {os.path.join(dirpath, file)} ...")
                self.parse_file(dirpath, file)


database = Database(
    db_user=DB_USER, db_pass=DB_PASS, host=DB_HOST, port=DB_PORT, database=DB_NAME
)
parser = Parser(database)


start = timer.time()
parser.parse_and_write_to_db()
end = timer.time()
LOGGER.info(f"Export took {end - start} seconds")

database.close_connection()
