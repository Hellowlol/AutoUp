

import os
import sqlite3
import threading
import time

import logger

FILENAME = "plexpy.db"
db_lock = threading.Lock()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d


class MonitorDatabase(object):

    def __init__(self, fp=None):
        self.filename = filename
        if fp is None:
            self.fp = 'xx.db'
        self.connection = sqlite3.connect(self.fp, timeout=20)
        # Don't wait for the disk to finish writing
        self.connection.execute("PRAGMA synchronous = OFF")
        # Journal disabled since we never do rollbacks
        # 64mb of cache memory, probably need to make it user configurable
        self.connection.execute("PRAGMA cache_size=-%s" % (1064 * 1024))
        self.connection.row_factory = dict_factory

    def action(self, query, args=None, return_last_id=False):
        if query is None:
            return

        with db_lock:
            sql_result = None
            attempts = 0

            while attempts < 5:
                try:
                    with self.connection as c:
                        if args is None:
                            sql_result = c.execute(query)
                        else:
                            sql_result = c.execute(query, args)
                    # Our transaction was successful, leave the loop
                    break

                except sqlite3.OperationalError as e:
                    if "unable to open database file" in e.message or "database is locked" in e.message:
                        logger.warn(u"PlexPy Database :: Database Error: %s", e)
                        attempts += 1
                        time.sleep(1)
                    else:
                        logger.error(u"PlexPy Database :: Database error: %s", e)
                        raise

                except sqlite3.DatabaseError as e:
                    logger.error(u"PlexPy Database :: Fatal Error executing %s :: %s", query, e)
                    raise

            return sql_result

    def create_table(self, table, args=''):
        self.action('CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY AUTOINCREMENT, %s)' % (table, args))

    def select(self, query, args=None):

        sql_results = self.action(query, args).fetchall()

        if sql_results is None or sql_results == [None]:
            return []

        return sql_results

    def select_single(self, query, args=None):

        sql_results = self.action(query, args).fetchone()

        if sql_results is None or sql_results == "":
            return ""

        return sql_results

    def upsert(self, table_name, value_dict, key_dict):

        trans_type = 'update'
        changes_before = self.connection.total_changes

        gen_params = lambda my_dict: [x + " = ?" for x in my_dict.keys()]

        update_query = "UPDATE " + table_name + " SET " + ", ".join(gen_params(value_dict)) + \
                       " WHERE " + " AND ".join(gen_params(key_dict))

        self.action(update_query, value_dict.values() + key_dict.values())

        if self.connection.total_changes == changes_before:
            trans_type = 'insert'
            insert_query = (
                "INSERT INTO " + table_name + " (" + ", ".join(value_dict.keys() + key_dict.keys()) + ")" +
                " VALUES (" + ", ".join(["?"] * len(value_dict.keys() + key_dict.keys())) + ")"
            )
            try:
                self.action(insert_query, value_dict.values() + key_dict.values())
            except sqlite3.IntegrityError:
                logger.info(u"PlexPy Database :: Queries failed: %s and %s", update_query, insert_query)

        # We want to know if it was an update or insert
        return trans_type