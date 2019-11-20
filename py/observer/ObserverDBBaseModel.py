# -----------------------------------------------------------------------------
# Name:        ObserverDBBaseModel.py
# Purpose:     Global APSW object for peewee
#
# Author:      Will Smith <will.smith@noaa.gov>
#
# Created:     March 4, 2016
# License:     MIT
# ------------------------------------------------------------------------------

import logging
import os

import apsw
import keyring
from peewee import *
from playhouse.apsw_ext import APSWDatabase
from py.observer.ObserverConfig import use_encrypted_database


def find_db_path():
        """
        Search expected paths for the .db file
        :return: full path + filename
        """
        db_filename = 'observer_encrypted.db' if use_encrypted_database else 'observer.db'
        # logger = logging.getLogger('__main__')
        if os.path.exists(os.path.join(os.getcwd(), '../data/' + db_filename)):
            path = '../data'
        elif os.path.exists(os.path.join(os.getcwd(), 'data/' + db_filename)):
            path = 'data'
        elif os.path.exists(os.path.join(os.getcwd(), '../../data/' + db_filename)):
            path = '../../data'  # Unit tests
        else:
            errmsg = 'Error locating database ' + db_filename
            logging.error(errmsg)
            raise FileNotFoundError(errmsg)

        return os.path.join(path, db_filename)


database = APSWDatabase(find_db_path(), **{})


def activate_encryption(db):
    """
    Activate SQLite Encryption Extension (SEE)
    @param db: APSW database object
    @return:
    """
    print('Encryption ENABLED.')
    obs_credentials_namespace = 'OPTECS v1'
    activate_keyname = 'see_activation'
    optecs_see_keyname = 'optecs_see_key'
    activate_key = keyring.get_password(obs_credentials_namespace, activate_keyname)
    optecs_key = keyring.get_password(obs_credentials_namespace, optecs_see_keyname)
    if not activate_key or not optecs_key:
        raise Exception('SQLite Encryption Extension Keys not found. Run (newest) set_optecs_sync_pw.py')
    else:
        c = db.get_cursor()
        c.execute(f"PRAGMA activate_extensions='{activate_key}';")
        c.execute(f"PRAGMA key = '{optecs_key}';")




def deactivate_WAL(db):
    """
    Make sure WAL is deactivated
    @param db: APSW database object
    """
    #
    c = db.get_cursor()
    c.execute('PRAGMA journal_mode=DELETE;')  # Consider MEMORY for perf boost, but danger of db corruption
    # print('DB Journaling set to default (DELETE).')

if use_encrypted_database:
    activate_encryption(database)

deactivate_WAL(database)

# Add a half-second timeout to allow background thread to access database.
# Background thread is responsible for completing all DB operations in less than half a second,
# or breaking up database accesses into smaller chunks, broken up by a call to timer.sleep(0.01)
# in order to all context switch to UI thread.
DATABASE_TIMEOUT = 5000
database.timeout = DATABASE_TIMEOUT


class BaseModel(Model):
    class Meta:
        database = database


def connect_orm():
    """
    Intended to be called from main
    """
    if database.is_closed():
        logging.info(f"ORM: Connecting to {find_db_path()}; timeout={database.timeout} seconds.")
        database.connect()
    else:
        logging.info('Already connected to DB')

def get_db_version_info():
    return (f"APSW version: {apsw.apswversion()}; " +
            f"SQLite lib version: {apsw.sqlitelibversion()}; " +
            f"SQLite header version: {apsw.SQLITE_VERSION_NUMBER}.")

def close_orm():
    """
    Intended to be called from main
    """
    logging.info("ORM: Closing connection " + find_db_path())
    database.close()
