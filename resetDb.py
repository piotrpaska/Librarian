from cryptography.fernet import Fernet
import sqlite3

passwordsDBconnection = sqlite3.connect('db.db')
passwordsDBcursor = passwordsDBconnection.cursor()

key = Fernet.generate_key()

with open('fernet_key.txt', 'wb') as keyFile:
    keyFile.write(key)

cipher = Fernet(key)

data = b'None'
adminData = b'admin'
encryptedata = cipher.encrypt(data)
adminEncryptedata = cipher.encrypt(adminData)
passwordsDBcursor.execute("UPDATE pwds SET username = ?, password=? WHERE type = 'mongo'", (encryptedata, encryptedata,))
passwordsDBcursor.execute("UPDATE pwds SET username = ?, password=? WHERE type = 'admin'", (adminEncryptedata, adminEncryptedata,))
passwordsDBconnection.commit()