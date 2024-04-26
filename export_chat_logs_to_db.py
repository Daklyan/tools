"""Script to export Chatterino logs to mariadb database"""

import os
import re
import sys
import time as timer
import logging

from datetime import datetime, date, time

import mariadb
import pytz


DB_HOST = "192.168.1.2"
DB_PORT = 3306
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_NAME = "chatlogs"
PATH_TO_LOGS = "/mnt/c/Users/bolos/AppData/Roaming/Chatterino2/Logs/Twitch/Channels/"

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s] - %(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[logging.FileHandler("export.log"), logging.StreamHandler()],
    encoding="utf-8",
    level=logging.INFO,
)


class Database:
    """Class to interact with mariadb Database"""

    def __init__(
        self, db_user: str, db_pass: str, database: str, host="127.0.0.1", port=3306
    ):
        try:
            self.__connection = mariadb.connect(
                user=db_user, password=db_pass, host=host, port=port, database=database
            )
            self.__cursor = self.__connection.cursor()
        except mariadb.Error as err:
            LOGGER.error(f"Error while connecting to database: {err}")
            sys.exit(1)

    def get_connection(self):
        """Get the database connection"""
        return self.__connection

    def get_cursor(self):
        """Returns the connection cursor"""
        return self.__cursor

    def close_connection(self):
        """Closes the database connection"""
        self.__connection.close()


class Parser:
    """Class to parse chatterino log files"""

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
            self.cur.execute("SELECT id FROM message WHERE file=? LIMIT 1", (filename,))
            if self.cur.fetchone():
                return True
        except mariadb.Error as err:
            LOGGER.error(f"Error fetching file in database: {err}")
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
                "INSERT INTO message (file, pseudo, message, channel, timestamp) VALUES (?, ?, ?, ?, ?)",
                list_of_values,
            )
            self.conn.commit()
        except mariadb.Error as err:
            LOGGER.error(f"Error while adding messages to database: {err}")

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

        if "-".join(date_us) == datetime.today().strftime("%Y-%m-%d"):
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
                    logged_lines.append((file, pseudo, message, channel, date_object))

                self.write_many_messages_to_db(list_of_values=logged_lines)
        except Exception as err:
            LOGGER.debug(f"Error while parsing {file}: {err}")

    def parse_and_write_to_db(self):
        """Go through every file of a given path and starts the parsing / writing to database"""
        for dirpath, _, files in os.walk(PATH_TO_LOGS):
            for file in files:
                if self.check_if_file_is_done(filename=file):
                    LOGGER.info(f"File {file} already exported, skipping!")
                    continue
                LOGGER.info(f"Processing {file} ...")
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
