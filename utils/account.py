"""
python version 3.9
"""

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC 
from cryptography.hazmat.backends import default_backend 
from cryptography.hazmat.primitives import hashes 
from cryptography.fernet import Fernet 
from hashlib import md5 
from web3 import Web3 
import base64 
import redis 
import json 

import logging

class Account :
    
    def __init__(self, password):

        self.password = password
        self._read_accounts()

    def _read_accounts(self ):

        try :
            with open('./accounts.json' ,'r') as fi:
                account = json.load(fi)    

        except Exception as e:
            logging.error(f'!! error in file accounts.json [{e}]')    
            exit(0)

        self._decode(account)


        logging.info(f"- successfully added account keys")

    def _decode(self ,ls_account):
        
        salt = b'fuckup_' 
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        
        if re := { 'public', 'private'} - set(ls_account[0].keys()) : 
            
            logging.error(f"!! can't found keys{re} in index account [{index}]") 
            exit(0) 
        
        try : 
    
            self.__public_key = Web3.toChecksumAddress(ls_account[0]['public']) 
            self.__private_key = Fernet(key).decrypt(ls_account[0]['private'].encode()).decode()   

        except Exception as e:

            logging.error(f"!! error in decode account fields -> [{e}]")
            exit(0)

    @property
    def private_key(self):

        return self.__private_key

    @property
    def public_key(self):

        return self.__public_key
    
    @property
    def api_key(self):

        return self.__api_key

    @property
    def api_secret(self):

        return self.__api_secret

