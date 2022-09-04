from consolemenu.items import FunctionItem, SubmenuItem, CommandItem
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from consolemenu import ConsoleMenu ,Screen
from cryptography.fernet import Fernet
from getpass import getpass
import base64
 

def encryptPrivate():

    Screen.printf('Enter your private key : ')
    privateKey = Screen.input('')

    Screen.printf('Enter your password : ')
    password = Screen.input('')
    password = password.encode() 

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fuckup_' ,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))

    privateKey = privateKey.encode()
    encrypted = Fernet(key).encrypt(privateKey)

    Screen.printf('\nEncrypted :',encrypted.decode() ,'\n' )
    password = Screen.input(0)



def decryptPrivate():

    Screen.printf('Enter your private key : ')
    privateKey = Screen.input('')

    Screen.printf('Enter your password : ')
    password = Screen.input('')
    password = password.encode() 

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fuckup_' ,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))

    decrypted = Fernet(key).decrypt(privateKey.encode())
    
    Screen.printf('\nDecrypted private key :',decrypted.decode() ,'\n' )
    password = Screen.input(0)

menu = ConsoleMenu("This is a menu!", "It has a subtitle too!")
encrypt_item = FunctionItem("Encrypt Private Key", encryptPrivate)
decrypt_item = FunctionItem("Decrypt Private Key", decryptPrivate)

menu.append_item(encrypt_item)
menu.append_item(decrypt_item)

menu.show()

