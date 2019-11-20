# Encrypt IFQDEV, IFQADMIN, IFQ databases

from subprocess import Popen, PIPE
import os
import keyring
from shutil import copyfile

def get_db_key():
    obs_credentials_namespace = 'OPTECS v1'
    optecs_see_keyname = 'optecs_see_key'
    return keyring.get_password(obs_credentials_namespace, optecs_see_keyname)

def encrypt_db(db_path, overwrite_file=False):
    see_path = r'..\bin\SQLite Encryption Extension\see.exe'
    if not os.path.isfile(db_path):
        print(f'Could not find {db_path}, skipping.')
        return
    if not os.path.isfile(see_path):
        print(f'Could not find {see_path}, aborting. This file needs to be acquired from team file share.')
        return

    db_path_encrypted = db_path.replace('.db', '_encrypted.db')
    if not overwrite_file and os.path.isfile(db_path_encrypted):
        print(f'{db_path_encrypted} already exists. Please delete and re-run encryption script.')
        return
    print(f'Copying {db_path} to {db_path_encrypted}...')
    copyresult = copyfile(db_path, db_path_encrypted)
    print(f'Wrote {copyresult}')

    enc_key = get_db_key()
    print(f'Encrypting {db_path_encrypted} with key {enc_key.replace(enc_key[:6], "******", 6)}')

    proc = Popen([see_path, copyresult], stdin=PIPE)
    rekey_text = f'.rekey "" {enc_key} {enc_key}\n.quit\n'
    proc.communicate(rekey_text.encode('utf-8'))

if __name__ == '__main__':
    database_path = r'..\data'
    databases_to_encrypt = ['clean_observer_IFQADMIN.db', 'clean_observer_IFQ.db', 'clean_observer_IFQ_TRAINING.db']

    for db in databases_to_encrypt:
        encrypt_db(os.path.join(database_path, db), overwrite_file=True)

