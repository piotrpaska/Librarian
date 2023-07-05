import json
import datetime
import prettytable
import msvcrt
import os
from dotenv import set_key, get_key, find_dotenv
import pymongo
import maskpass
from colorama import Fore, Style, Back, init
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from keycloak import KeycloakOpenID, KeycloakAdmin
import atexit
import yaml
import sqlite3

# Mongo variables
global isJson
global client
global db
global activeCollection
global historyCollection
global mongoUsersCollection

global profileUsername
global profilePassword

global viewerRole
global librarianRole

global token
global keycloak_openid

with open('config.yml', 'r') as f:
    yamlFile = yaml.safe_load(f)

# Json variables
activeHiresFile = yamlFile['active_hires_file_name']
historyFile = yamlFile['history_file_name']
dateFormat = yamlFile['date_format']

senderEmail = yamlFile['sender_email']
receiveEmail = yamlFile['admins_emails']
senderPassword = yamlFile['sender_password']

keycloak_openid = KeycloakOpenID

viewerRole = yamlFile['viewer_role_name']
librarianRole = yamlFile['librarian_role_name']
adminRole = yamlFile['admin_role_name']

keycloakServerUrl = yamlFile['keycloak']['server_url']
keycloakRealm = yamlFile['keycloak']['realm_name']

passwordsDBconnection = sqlite3.connect('database.db')
passwordsDBcursor = passwordsDBconnection.cursor()

passwordsDBconnection.execute("""SELECT * FROM passwords WHERE username='admin'""")
adminPassword = passwordsDBcursor.fetchone()

init()
class AdminTools:

    def __init__(self, senderEmail: str, receiveEmail: list, password: str):
        self.senderEmail = senderEmail
        self.receiveEmail = receiveEmail
        self.password = password

    def emailCodeSend(self) -> bool:
        confirmCode = str(random.randint(100000, 999999))
        # Tworzenie wiadomości
        message = MIMEMultipart()
        message['From'] = self.senderEmail
        message['To'] = ', '.join(self.receiveEmail)
        message['Subject'] = 'Librarian admin'
        body = f"""<h1>There is your confirmation code for librarian</h1><font size:"16">Here is your confirmation code: <b>{confirmCode}</b></font>"""
        message.attach(MIMEText(body, 'html'))

        # Utworzenie sesji SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.senderEmail, self.password)


        # Wysłanie wiadomości
        text = message.as_string()
        server.sendmail(self.senderEmail, self.receiveEmail, text)
        server.quit()

        print("Enter confirmation code from email: ", end='', flush=True)  # use print instead of input to avoid blocking
        codeInput = ""
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    print()
                    break  # exit loop
                elif key == 8:  # backspace key
                    if len(codeInput) > 0:
                        codeInput = codeInput[:-1]
                        print(f"\rEnter confirmation code from email: {codeInput} {''}\b", end='', flush=True)
                else:
                    codeInput += chr(key)
                    print(chr(key), end='', flush=True)

        return codeInput == confirmCode

    global keycloakAdmin
    keycloakAdmin = KeycloakAdmin(server_url=keycloakServerUrl,
                                  username=yamlFile['keycloak']['admin']['username'],
                                  password=yamlFile['keycloak']['admin']['password'],
                                  realm_name=keycloakRealm,
                                  verify=True
                                  )

    def checkRole(self, roleName: str, username: str) -> bool:
        global keycloakAdmin
        # Pobranie ID użytkownika na podstawie jego nazwy użytkownika
        user_id = keycloakAdmin.get_user_id(username)

        # Pobranie ról na poziomie królestwa dla użytkownika
        realm_roles = keycloakAdmin.get_realm_roles_of_user(user_id=user_id)

        # Sprawdzenie, czy użytkownik posiada rolę "librarian" na poziomie królestwa
        if any(role['name'] == roleName for role in realm_roles):
            return True
        else:
            return False

    def addProfile(self):
        global keycloakAdmin

        print()
        print(f'{Fore.LIGHTWHITE_EX}Adding user{Style.RESET_ALL}')
        username = input('Enter username: ')
        password = maskpass.askpass(prompt='Enter password: ', mask='*')
        email = input('Enter email: ')
        firstName = input('Enter first name: ')
        lastName = input('Enter last name: ')
        while True:
            print(f'{Fore.LIGHTWHITE_EX}Roles{Style.RESET_ALL}\n'
                  '[1] - Viewer\n'
                  '[2] - Librarian\n'
                  '[3] - admin')
            roles = int(input('Select from list above: '))

            if roles in range(0, 4):
                break
            else:
                print(f'{Fore.RED}Nie ma takiej opcji.{Style.RESET_ALL}')
                print()
        isEmailVerified = True

        if email != '':
            #Weryfikacja email-a
            verifyCode = str(random.randint(100000, 999999))
            # Tworzenie wiadomości
            message = MIMEMultipart()
            message['From'] = self.senderEmail
            message['To'] = ', '.join(self.receiveEmail)
            message['Subject'] = 'Librarian admin'
            body = f"""<h1>There is your confirmation code for librarian</h1><font size:"16">Here is your confirmation code: <b>{verifyCode}</b></font>"""
            message.attach(MIMEText(body, 'html'))

            # Utworzenie sesji SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.senderEmail, self.password)

            # Wysłanie wiadomości
            text = message.as_string()
            server.sendmail(self.senderEmail, self.receiveEmail, text)
            server.quit()

            i = 3
            while i > 0:
                verifyCodeInput = input('Enter email verify code: ')
                if verifyCode == verifyCodeInput:
                    isEmailVerified = True
                    break
                else:
                    if i > 0:
                        i = i - 1
                        print(f'{Fore.RED}Wrong verify code. Remaining trials: {i}{Style.RESET_ALL}')
                        print()
                    else:
                        print(f'{Fore.RED}Wrong verify code. Adding user canceled{Style.RESET_ALL}')
                        isEmailVerified = False

        if isEmailVerified == False:
            print(f"{Fore.RED}Adding user canceled{Style.RESET_ALL}")
            return

        #creating user
        user = {"username": username,
                "email": email,
                "enabled": True,
                "firstName": firstName,
                "lastName": lastName,
                "emailVerified": isEmailVerified}

        keycloakAdmin.create_user(user)

        #Adding password
        user_id = keycloakAdmin.get_user_id(username)

        keycloakAdmin.set_user_password(user_id, password, temporary=False)

        global viewerRole
        global librarianRole
        global adminRole

        if roles == 1:
            keycloakAdmin.assign_realm_roles(user_id=user_id, roles=[{'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        elif roles == 2:
            keycloakAdmin.assign_realm_roles(user_id=user_id, roles=[{'id': '093d1d40-60ef-4af4-8970-f2e0f4cfc053', 'name': 'librarian', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        elif roles == 3:
            keycloakAdmin.assign_realm_roles(user_id=user_id, roles=[{'id': '093d1d40-60ef-4af4-8970-f2e0f4cfc053', 'name': 'librarian', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '8bfa8729-d769-4363-9243-6fee6d8f6282', 'name': 'admin', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        print(f'{Fore.LIGHTGREEN_EX}Added profile{Style.RESET_ALL}')


    def deleteProfile(self):
        global keycloakAdmin

        usersList = prettytable.PrettyTable(["Username"])
        usersIDs = []

        users = keycloakAdmin.get_users()
        for user in users:
            usersList.add_row([user["username"]])
            usersIDs.append(user)
        usersList.add_autoindex("ID")
        usersList.title = "Users list"

        print(usersList)
        print("Enter user ID that you want to delete: ", end='',
              flush=True)  # use print instead of input to avoid blocking
        id = ""
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    if id.isdigit():
                        print()
                        break  # exit loop
                    else:
                        continue
                elif key == 8:  # backspace key
                    if len(id) > 0:
                        id = id[:-1]
                        print(f"\rEnter user ID that you want to delete: {id} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    id += chr(key)
                    print(chr(key), end='', flush=True)

        keycloakAdmin.delete_user(usersIDs[int(id) - 1]['id'])
        print(f'{Fore.LIGHTGREEN_EX}Deleted profile{Style.RESET_ALL}')


    def modifyProfile(self):
        #TODO: dodać możliwość zmiany roli
        global keycloakAdmin

        usersList = prettytable.PrettyTable(["Username"])
        usersIDs = []

        users = keycloakAdmin.get_users()
        for user in users:
            usersList.add_row([user["username"]])
            usersIDs.append(user)
        usersList.add_autoindex("ID")
        usersList.title = "Users list"

        print(usersList)
        print("Enter user ID that you want to delete: ", end='',
              flush=True)  # use print instead of input to avoid blocking
        id = ""
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    if id.isdigit():
                        print()
                        break  # exit loop
                    else:
                        continue
                elif key == 8:  # backspace key
                    if len(id) > 0:
                        id = id[:-1]
                        print(f"\rEnter user ID that you want to delete: {id} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    id += chr(key)
                    print(chr(key), end='', flush=True)

        chosenUser = usersIDs[int(id) - 1]

        print("Enter username: ", end='', flush=True)  # use print instead of input to avousername blocking
        username = chosenUser["username"]
        print(f"\rEnter username: {username} {''}\b", end='', flush=True)
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    print()
                    break  # exit loop
                elif key == 8:  # backspace key
                    if len(username) > 0:
                        username = username[:-1]
                        print(f"\rEnter username: {username} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    username += chr(key)
                    print(chr(key), end='', flush=True)

        print("Enter email: ", end='', flush=True)  # use print instead of input to avoemail blocking
        email = ''
        if 'email' in chosenUser:
            email = chosenUser["email"]
        print(f"\rEnter email: {email} {''}\b", end='', flush=True)
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    print()
                    break  # exit loop
                elif key == 8:  # backspace key
                    if len(email) > 0:
                        email = email[:-1]
                        print(f"\rEnter email: {email} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    email += chr(key)
                    print(chr(key), end='', flush=True)

        print("Enter first name: ", end='', flush=True)  # use print instead of input to avofirstName blocking
        firstName = chosenUser["firstName"]
        print(f"\rEnter first name: {firstName} {''}\b", end='', flush=True)
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    print()
                    break  # exit loop
                elif key == 8:  # backspace key
                    if len(firstName) > 0:
                        firstName = firstName[:-1]
                        print(f"\rEnter first name: {firstName} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    firstName += chr(key)
                    print(chr(key), end='', flush=True)

        print("Enter last name: ", end='', flush=True)  # use print instead of input to avolastName blocking
        lastName = chosenUser["lastName"]
        print(f"\rEnter last name: {lastName} {''}\b", end='', flush=True)
        while True:
            if msvcrt.kbhit():
                key = ord(msvcrt.getch())
                if key == 27:  # escape key
                    print()
                    os.system('cls')
                    return  # exit function
                elif key == 13:  # enter key
                    print()
                    break  # exit loop
                elif key == 8:  # backspace key
                    if len(lastName) > 0:
                        lastName = lastName[:-1]
                        print(f"\rEnter last name: {lastName} {''}\b", end='', flush=True)
                elif key == 224:  # special keys (arrows, function keys, etc.)
                    key = ord(msvcrt.getch())
                    if key == 72:  # up arrow key
                        continue
                    elif key == 80:  # down arrow key
                        continue
                    elif key == 75:  # left arrow key
                        continue
                    elif key == 77:  # right arrow key
                        continue
                else:
                    lastName += chr(key)
                    print(chr(key), end='', flush=True)

        while True:
            print(f'{Fore.LIGHTWHITE_EX}Roles{Style.RESET_ALL}\n'
                  '[1] - Viewer\n'
                  '[2] - Librarian\n'
                  '[3] - admin')
            roles = int(input('Select from list above: '))

            if roles in range(0, 4):
                break
            else:
                print(f'{Fore.RED}Nie ma takiej opcji.{Style.RESET_ALL}')
                print()

        updatePayload = {"username": username,
                         "firstName": firstName,
                         "lastName": lastName
                         }
        if email != '':
            updatePayload["email"] = email
        else:
            updatePayload["email"] = ''

        realm_roles = keycloakAdmin.get_realm_roles_of_user(user_id=chosenUser['id'])
        for role in realm_roles:
            keycloakAdmin.delete_realm_roles_of_user(user_id=chosenUser['id'], roles=[role])
        keycloakAdmin.update_user(user_id=chosenUser['id'], payload=updatePayload)
        if roles == 1:
            keycloakAdmin.assign_realm_roles(user_id=chosenUser['id'], roles=[{'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        elif roles == 2:
            keycloakAdmin.assign_realm_roles(user_id=chosenUser['id'], roles=[{'id': '093d1d40-60ef-4af4-8970-f2e0f4cfc053', 'name': 'librarian', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        elif roles == 3:
            keycloakAdmin.assign_realm_roles(user_id=chosenUser['id'], roles=[{'id': '093d1d40-60ef-4af4-8970-f2e0f4cfc053', 'name': 'librarian', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '8bfa8729-d769-4363-9243-6fee6d8f6282', 'name': 'admin', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'},
                                                                     {'id': '52edcaf1-5c34-42dc-8cd0-168637c79da4', 'name': 'viewer', 'description': '', 'composite': False, 'clientRole': False, 'containerId': 'librarian-keycloak'}])
        print(f'{Fore.LIGHTGREEN_EX}Modified profile{Style.RESET_ALL}')


    def changePassword(self, username):
        try:
            global keycloakAdmin
            user_id = keycloakAdmin.get_user_id(username)
            keycloakAdmin.send_update_account(user_id=user_id, payload=['UPDATE_PASSWORD'])
            print(f'{Fore.GREEN}Udało się wysłać email.\n'
                  f'Zobacz swoją skrzynkę pocztową i postępuj zgodnie z instruckjami zawartymi w email-u{Style.RESET_ALL}')
        except Exception:
            print(f'{Fore.RED}Zmiana hasła niepowiodła się. Możliwe że nie masz przypisanego adresu email do profilu\n'
                  f'Poproś administratora o pomoc{Style.RESET_ALL}')
            isEnd = False
            while isEnd == False:
                adminEmailChoice = input(f'Jeśli jest obok ciebie administrator wpisz? (y/n): ')
                if adminEmailChoice == 'y':
                    i = 3
                    while i > 0:
                        adminPasswordInput = maskpass.askpass('Wpisz hasło administratora: ', '*')
                        if adminPasswordInput == adminPassword:
                            print()
                            while True:
                                newPassword = input('Wpisz nowe hasło: ')
                                repeatNewPassword = maskpass.askpass('Powtórz nowe hasło: ', '*')
                                if newPassword == repeatNewPassword:
                                    keycloakAdmin.set_user_password(user_id=user_id, password=newPassword, temporary=False)
                                    print(f'{Fore.GREEN}Pomyślnie zmieniono hasło{Style.RESET_ALL}')
                                    isEnd = True
                                    break
                                else:
                                    print(f'{Fore.RED}Hasła się różnią.{Style.RESET_ALL}')
                                    print()
                            break
                        else:
                            i = i - 1
                            if i > 0:
                                print(f'{Fore.RED}Pozostałe próby: {i}{Style.RESET_ALL}')
                            else:
                                print(f'{Fore.RED}Zmiana hasła została anulowana.{Style.RESET_ALL}')
                                isEnd = True
                                break
                elif adminEmailChoice == 'n':
                    print(f'{Fore.RED}Zmiana hasła została anulowana.{Style.RESET_ALL}')
                    break
                else:
                    print(f'{Fore.RED}Niepoprawna komenda.{Style.RESET_ALL}')

    def changeAdminPassword(self):
        global passwordsDBconnection
        global passwordsDBcursor
        global adminPassword
        confirmPassword = maskpass.askpass('Enter current admin password: ', '*')
        if confirmPassword == adminPassword:
            while True:
                newPassword = maskpass.askpass('Enter new password: ', '*')
                repeatPassword = maskpass.askpass('Repeat password: ', '*')

                if newPassword == repeatPassword:
                    passwordsDBcursor.execute(f"UPDATE passwords SET password=? WHERE username = 'admin'", (newPassword,))
                    passwordsDBconnection.commit()
                    adminPassword = newPassword
                    break
                else:
                    print(f"""{Fore.RED}Passwords don't match{Style.RESET_ALL}""")
        else:
            print(f"""{Fore.RED}Incorrect password{Style.RESET_ALL}""")
    def changeMode(self):
        try:
            if self.emailCodeSend():
                print(f'{Fore.GREEN}Auth confirmed{Style.RESET_ALL}')
                if get_key(find_dotenv(), 'JSON') == 'True':
                    set_key(find_dotenv(), 'JSON', 'False')
                elif get_key(find_dotenv(), 'JSON') == 'False':
                    set_key(find_dotenv(), 'JSON', 'True')
                print(f'{Fore.GREEN}Mode changed successfully{Style.RESET_ALL}')
                print('Please restart program')
            else:
                print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")
        except Exception:
            print('Czas minął')

    def resetActive(self):
        try:
            if not isJson:
                if self.emailCodeSend():
                    print(f'{Fore.GREEN}Auth confirmed{Style.RESET_ALL}')
                    activeCollection.delete_many({})
                    print(f'{Fore.GREEN}Active rents list is clear{Style.RESET_ALL}')
                else:
                    print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")
            else:
                print(f"{Fore.RED}You aren't in MongoDB mode{Style.RESET_ALL}")
        except Exception:
            print('Czas minął')
            print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")

    def resetHistory(self):
        try:
            if not isJson:
                if self.emailCodeSend():
                    print(f'{Fore.GREEN}Auth confirmed{Style.RESET_ALL}')
                    historyCollection.delete_many({})
                    print(f'{Fore.GREEN}History is clear{Style.RESET_ALL}')
                else:
                    print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")
            else:
                print(f"{Fore.RED}You aren't in MongoDB mode{Style.RESET_ALL}")
        except Exception:
            print('Czas minął')
            print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")

    def resetAll(self):
        try:
            if not isJson:
                if self.emailCodeSend():
                    print(f'{Fore.GREEN}Auth confirmed{Style.RESET_ALL}')
                    activeCollection.delete_many({})
                    historyCollection.delete_many({})
                    print(f'{Fore.GREEN}Database is fully reset{Style.RESET_ALL}')
                else:
                    print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")
            else:
                print(f"{Fore.RED}You aren't in MongoDB mode{Style.RESET_ALL}")
        except Exception:
            print('Czas minął')
            print(f"""{Fore.RED}You don't have permissions{Style.RESET_ALL}""")

def profiles():
    # Konfiguracja klienta Keycloak
    keycloak_url = keycloakServerUrl
    realm_name = keycloakRealm
    client_id = yamlFile['keycloak']['openID']['client_id']
    client_secret = yamlFile['keycloak']['openID']['client_secret']

    # Inicjalizacja obiektu
    global keycloak_openid
    keycloak_openid = KeycloakOpenID(server_url=keycloak_url, client_id=client_id, realm_name=realm_name,
                                     client_secret_key=client_secret)

    # Logowanie
    def checkToken(username, password):
        try:
            global token
            token = keycloak_openid.token(username, password)
            return True
        except Exception as error:
            return False

    while True:
        print(f'{Fore.LIGHTWHITE_EX}Zaloguj się za pomocą twojego profilu. Jeśli nie pamiętasz hasła wpisz "cp":{Style.RESET_ALL}')
        inputUsername = input('Wpisz login lub "cp" w celu zmiany hasła: ')
        if inputUsername == 'cp':
            usernmeForChangePassword = input('Wpisz login: ')
            print()
            adminTools.changePassword(usernmeForChangePassword)
            print()
            print(f'{Fore.LIGHTWHITE_EX}Jeśli zmieniłeś już hasło zaloguj się ponownie z nowym hasłem{Style.RESET_ALL}')
            print()

        if inputUsername != 'cp':
            inputPassword = maskpass.askpass('Wpisz hasło: ', '*')

            if checkToken(inputUsername, inputPassword):
                global profileUsername
                global profilePassword
                userinfo = keycloak_openid.userinfo(token['access_token'])
                profileUsername = userinfo['preferred_username']
                profilePassword = inputPassword
                os.system('cls')
                break
            else:
                print(f'{Fore.RED}Niepoprawny login lub hasło.{Style.RESET_ALL}')
                print()
                continue



def mongoPreconfiguration():
    connectionString = str
    dotenv_path = find_dotenv()
    global isJson
    if get_key(dotenv_path, 'JSON') == 'True':
        isJson = True
    else:
        isJson = False
    if not isJson:
        userInput = get_key(dotenv_path, 'MONGODB_USER')
        passwordInput = get_key(dotenv_path, 'MONGODB_PASSWORD')
        if userInput == 'None' and passwordInput == 'None':
            while True:
                print(f'{Fore.LIGHTWHITE_EX}Konfiguracja dostępu do bazy danych{Style.RESET_ALL}')
                userInput = input("Podaj nazwę użytkownika: ")
                passwordInput = maskpass.askpass(prompt='Podaj hasło do bazy danych MongoDB: ', mask='*')
                #TODO: Replace <password to default>
                connectionString = ''
                connectionString = yamlFile['mongodb_connection_string'].replace('<username>', 'default').replace('<password>', 'default')
                usersClient = pymongo.MongoClient(connectionString)
                usersDb = usersClient.Users
                usersCollection = usersDb.users
                usersDict = usersCollection.find_one({"username": str(userInput), "password": str(passwordInput)})
                if usersDict != None:
                    set_key(dotenv_path, "MONGODB_USER", userInput)
                    set_key(dotenv_path, "MONGODB_PASSWORD", passwordInput)
                    break
                else:
                    print()
                    print(f"{Fore.RED}Nazwa użytkownika lub hasło jest niepoprawne{Style.RESET_ALL}")
                    print("----------------------------------------------------------------------------")
                    continue

        try:
            connectionString = yamlFile['mongodb_connection_string'].replace('<username>', userInput).replace('<password>', passwordInput)
            global client
            global db
            global activeCollection
            global historyCollection
            global mongoUsersCollection
            client = pymongo.MongoClient(connectionString)
            # TODO Check target database
            db = client[yamlFile['mongo_rents_db_name']]
            activeCollection = db[yamlFile['active_rents_collection_name']]
            historyCollection = db['history_rents_collection_name']
            mongoUsersCollection = client[yamlFile['mongo_users_db']][yamlFile['mongo_users_collection']]
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)


def addHire():
    """Zapisywane dane to: imię, nazwisko, klasa, tytuł książki, data wypożyczenia, kaucja"""
    sure = 0
    hireData = {}

    # imię
    print("Wpisz imię: ", end='', flush=True)  # use print instead of input to avoid blocking
    name = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                break  # exit loop
            elif key == 8:  # backspace key
                if len(name) > 0:
                    name = name[:-1]
                    print(f"\rWpisz imię: {name} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                name += chr(key)
                print(chr(key), end='', flush=True)

    hireData["name"] = name

    # nazwisko
    print("Wpisz nazwisko: ", end='', flush=True)  # use print instead of input to avoid blocking
    lastName = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                break  # exit loop
            elif key == 8:  # backspace key
                if len(lastName) > 0:
                    lastName = lastName[:-1]
                    print(f"\rWpisz nazwisko: {lastName} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                lastName += chr(key)
                print(chr(key), end='', flush=True)

    hireData["lastName"] = lastName

    print("Podaj klasę czytelnika (np. 2a): ", end='', flush=True)  # use print instead of input to avoid blocking
    klasa = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                break  # exit loop
            elif key == 8:  # backspace key
                if len(klasa) > 0:
                    klasa = klasa[:-1]
                    print(f"\rPodaj klasę czytelnika (np. 2a): {klasa} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                klasa += chr(key)
                print(chr(key), end='', flush=True)

    hireData["klasa"] = klasa

    # tytuł książki
    print("Wpisz tytuł wypożyczonej książki: ", end='', flush=True)  # use print instead of input to avoid blocking
    bookTitle = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                break  # exit loop
            elif key == 8:  # backspace key
                if len(bookTitle) > 0:
                    bookTitle = bookTitle[:-1]
                    print(f"\rWpisz tytuł wypożyczonej książki: {bookTitle} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                bookTitle += chr(key)
                print(chr(key), end='', flush=True)

    hireData["bookTitle"] = bookTitle

    print("Wpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): ", end='',
          flush=True)  # use print instead of input to avoid blocking
    deposit = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                if deposit == '' or deposit.isdigit() == True:
                    print()
                    break  # exit loop
            elif key == 8:  # backspace key
                if len(deposit) > 0:
                    deposit = deposit[:-1]
                    print(f"\rWpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): {deposit} {''}\b", end='',
                          flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                deposit += chr(key)
                print(chr(key), end='', flush=True)

    isDeposit = bool
    if deposit == '':
        hireData["deposit"] = 'Brak'
        isDeposit = False
    else:
        hireData["deposit"] = str(deposit) + "zl"
        isDeposit = True

    # ustawienie daty wypożyczenia
    rentalDate = datetime.date.today()
    maxReturnDate = rentalDate + datetime.timedelta(weeks=2)
    hireData["rentalDate"] = str(f"{rentalDate.strftime(dateFormat)}")
    if isDeposit:
        hireData["maxDate"] = str(f"{maxReturnDate.strftime(dateFormat)}")
    else:
        hireData["maxDate"] = '14:10'

    summary = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja'])
    summary.add_row(
        [hireData["name"], hireData["lastName"], hireData["klasa"], hireData["bookTitle"], hireData["rentalDate"],
         hireData["maxDate"], hireData["deposit"]])
    print(summary)

    while True:
        try:
            print("[1] - tak")
            print("[0] - nie")

            sure = int(input("Na pewno chcesz dodać nowego czytelnika? "))
            if sure != 1 and sure != 0:
                raise Exception
            break
        except Exception:
            print(f"{Fore.RED}Nie znaleziono takiej komendy. Spróbuj ponownie.{Style.RESET_ALL}")
            continue

    if isJson:
        if sure == 1:
            try:
                with open(activeHiresFile, "r") as f:
                    temp = json.load(f)
                    temp.append(hireData)
                with open(activeHiresFile, "w") as f:
                    json.dump(temp, f, indent=4)
                print(f'{Fore.GREEN}Dodano wypożyczenie{Style.RESET_ALL}')
            except Exception as error:
                print(Fore.RED + str(error) + Style.RESET_ALL)
        elif sure == 0:
            print(f"{Fore.GREEN}Anulowano dodanie wypożyczenia{Style.RESET_ALL}")
    else:
        if sure == 1:
            try:
                activeCollection.insert_one(hireData)
            except Exception as error:
                print(Fore.RED + str(error) + Style.RESET_ALL)
            else:
                print(f'{Fore.GREEN}Dodano wypożyczenie{Style.RESET_ALL}')
        elif sure == 0:
            print(f"{Fore.GREEN}Anulowano dodanie wypożyczenia{Style.RESET_ALL}")


def endHire():
    if isJson:
        with open(activeHiresFile, "r") as f:
            viewActiveHires()
            temp = json.load(f)
            data_length = len(temp)
    else:
        documentIDs = viewActiveHires()
        try:
            data_length = activeCollection.count_documents({})
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)

    if data_length <= 0:
        return

    print(f"Wybierz ID 1-{data_length}: ", end='', flush=True)  # use print instead of input to avoid blocking
    documentChoice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                delOptRange = range(1, int(data_length + 1))
                if int(documentChoice) in delOptRange:
                    print()
                    break  # exit loop
                else:
                    continue
            elif key == 8:  # backspace key
                if len(documentChoice) > 0:
                    documentChoice = documentChoice[:-1]
                    print(f"\rWybierz ID 1-{data_length}: {documentChoice} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                documentChoice += chr(key)
                print(chr(key), end='', flush=True)

    if isJson:
        new_data = []
        i = 1
        for entry in temp:
            if i == int(documentChoice):
                entry["returnDate"] = datetime.datetime.today().strftime(dateFormat)
                with open(historyFile, "r") as f:
                    temp = json.load(f)
                    temp.append(entry)
                with open(historyFile, "w") as f:
                    json.dump(temp, f, indent=4)
                i = i + 1
            else:
                new_data.append(entry)
                i = i + 1
            with open(activeHiresFile, "w") as f:
                json.dump(new_data, f, indent=4)
        print(f'{Fore.GREEN}Zakończono wypożyczenie{Style.RESET_ALL}')
    else:
        try:
            chosenDocument = activeCollection.find_one({'_id': documentIDs[int(documentChoice) - 1]["_id"]})
            returnDate = datetime.datetime.now()
            chosenDocument["returnDate"] = datetime.datetime.today().strftime(dateFormat)
            historyCollection.insert_one(chosenDocument)
            activeCollection.delete_one({'_id': chosenDocument['_id']})
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        else:
            print(f'{Fore.GREEN}Zakończono wypożyczenie{Style.RESET_ALL}')


def viewActiveHires():
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja', 'Status'])
    results.title = 'Trwające wypożyczenia'
    if isJson:
        with open(activeHiresFile, 'r') as f:
            jsonFile = json.load(f)
        for item in jsonFile:
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]

            overdue = ''
            maxDate = None

            # overdue
            today = None
            if maxDateSTR != '14:10':
                # jeśli kaucja jest wpłacona
                today = datetime.datetime.today().date()
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
            else:
                # jeśli kaucja nie została wpłacona
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat).date()
                today = datetime.datetime.today().date()
                if rentalDate < today:
                    difference = today - rentalDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            results.add_row(
                [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
    else:
        documentIDs = []
        try:
            entries = activeCollection.find()
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        for item in entries:
            documentIDs.append(item)  # pamiatac o numeracji od 0 w tablicy IDkow a od 1 w tabeli co się wyswietla !!!!
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]

            # overdue
            overdue = ''
            maxDate = None
            today = None
            if maxDateSTR != '14:10':
                # jeśli kaucja jest wpłacona
                today = datetime.datetime.today().date()
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
            else:
                # jeśli kaucja nie została wpłacona
                today = datetime.datetime.today().date()
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat).date()
                if rentalDate < today:
                    difference = today - rentalDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            results.add_row(
                [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])

    results.add_autoindex('ID')
    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)

    if not isJson:
        return documentIDs


def viewHistoryHires():
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Data zwrotu', 'Kaucja'])
    results.title = 'Historia wypożyczeń'
    if isJson:
        with open(historyFile, 'r') as f:
            jsonFile = json.load(f)
        for item in jsonFile:
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDate = item["rentalDate"]
            maxDate = item["maxDate"]
            returnDate = item["returnDate"]
            deposit = item["deposit"]
            results.add_row(
                [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
    else:
        try:
            entries = historyCollection.find()
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        for item in entries:
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDate = item["rentalDate"]
            maxDate = item["maxDate"]
            returnDate = item["returnDate"]
            deposit = item["deposit"]
            results.add_row(
                [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])

    results.add_autoindex('ID')
    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)


def activeSearch():
    print('[1] - imię')
    print('[2] - nazwisko')
    print('[3] - klasa')
    print('[4] - tytuł książki')

    print("Po czym chcesz szukać: ", end='', flush=True)  # use print instead of input to avoid blocking
    choice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                if int(choice) in range(1, 5):
                    print()
                    break  # exit loop
                else:
                    continue
            elif key == 8:  # backspace key
                if len(choice) > 0:
                    choice = choice[:-1]
                    print(f"\rPo czym chcesz szukać: {choice} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                choice += chr(key)
                print(chr(key), end='', flush=True)

    print("Wprowadź szukaną frazę: ", end='', flush=True)  # use print instead of input to avoid blocking
    phrase = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                phrase = phrase
                break  # exit loop
            elif key == 8:  # backspace key
                if len(phrase) > 0:
                    phrase = phrase[:-1]
                    print(f"\rWprowadź szukaną frazę: {phrase} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                phrase += chr(key)
                print(chr(key), end='', flush=True)
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja', 'Status'])
    results.title = f'Szukana fraza: {phrase}'
    with open(activeHiresFile, 'r') as f:
        jsonFile = json.load(f)

    if isJson:
        for item in jsonFile:

            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]

            overdue = ''
            maxDate = None
            today = None
            if maxDateSTR != '14:10':
                today = datetime.datetime.today().date()
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
            else:
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat).date()
                today = datetime.datetime.today().date()
                if rentalDate < today:
                    difference = today - rentalDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            if choice == str("1"):
                if str(phrase) in name:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("2"):
                if str(phrase) in lastName:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("3"):
                if str(phrase) in rentClass:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("4"):
                if str(phrase) in bookTitle:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
    else:
        try:
            entries = activeCollection.find()
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        for item in entries:

            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]

            overdue = ''
            maxDate = None
            today = None
            if maxDateSTR != '14:10':
                today = datetime.datetime.today().date()
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
            else:
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat).date()
                today = datetime.datetime.today().date()
                if rentalDate < today:
                    difference = today - rentalDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            if choice == str("1"):
                if str(phrase) in name:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("2"):
                if str(phrase) in lastName:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("3"):
                if str(phrase) in rentClass:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            if choice == str("4"):
                if str(phrase) in bookTitle:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])

    if len(results.rows) <= 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)


def historySearch():
    print('[1] - imię')
    print('[2] - nazwisko')
    print('[3] - klasa')
    print('[4] - tytuł książki')

    print("Po czym chcesz szukać: ", end='', flush=True)  # use print instead of input to avoid blocking
    choice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                if int(choice) in range(1, 5):
                    print()
                    break  # exit loop
                else:
                    continue
            elif key == 8:  # backspace key
                if len(choice) > 0:
                    choice = choice[:-1]
                    print(f"\rPo czym chcesz szukać: {choice} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                choice += chr(key)
                print(chr(key), end='', flush=True)

    print("Wprowadź szukaną frazę: ", end='', flush=True)  # use print instead of input to avoid blocking
    phrase = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                print()
                phrase = phrase
                break  # exit loop
            elif key == 8:  # backspace key
                if len(phrase) > 0:
                    phrase = phrase[:-1]
                    print(f"\rWprowadź szukaną frazę: {phrase} {''}\b", end='', flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                phrase += chr(key)
                print(chr(key), end='', flush=True)
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Data zwrotu', 'Kaucja'])
    results.title = f'Szukana fraza: {phrase}'
    with open(historyFile, 'r') as f:
        jsonFile = json.load(f)

    if isJson:
        for item in jsonFile:

            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDate = item["rentalDate"]
            maxDate = item["maxDate"]
            returnDate = item['returnDate']
            deposit = item["deposit"]

            if choice == str("1"):
                if str(phrase) in name:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("2"):
                if str(phrase) in lastName:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("3"):
                if str(phrase) in rentClass:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("4"):
                if str(phrase) in bookTitle:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
    else:
        try:
            entries = historyCollection.find()
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        for item in entries:

            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDate = item["rentalDate"]
            maxDate = item["maxDate"]
            returnDate = item['returnDate']
            deposit = item["deposit"]

            if choice == str("1"):
                if str(phrase) in name:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("2"):
                if str(phrase) in lastName:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("3"):
                if str(phrase) in rentClass:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])
            if choice == str("4"):
                if str(phrase) in bookTitle:
                    results.add_row(
                        [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), str(returnDate), deposit])

    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)


def addDeposit():
    if isJson:
        with open(activeHiresFile, "r") as f:
            viewActiveHires()
            temp = json.load(f)
            data_length = len(temp)
    else:
        documentIDs = viewActiveHires()
        try:
            data_length = activeCollection.count_documents({})
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)

    if data_length <= 0:
        return

    print("Wpisz ID wypożyczenia w którym chcesz dodać kaucję: ", end='',
          flush=True)  # use print instead of input to avoid blocking
    documentChoice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                idRange = range(1, int(data_length + 1))
                if int(documentChoice) in idRange:
                    print()
                    break  # exit loop
            elif key == 8:  # backspace key
                if len(documentChoice) > 0:
                    documentChoice = documentChoice[:-1]
                    print(f"\rWpisz ID wypożyczenia w którym chcesz dodać kaucję: {documentChoice} {''}\b", end='',
                          flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                documentChoice += chr(key)
                print(chr(key), end='', flush=True)

    print("Wpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): ", end='',
          flush=True)  # use print instead of input to avoid blocking
    deposit = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                if deposit == '' or deposit.isdigit() == True:
                    print()
                    break  # exit loop
            elif key == 8:  # backspace key
                if len(deposit) > 0:
                    deposit = deposit[:-1]
                    print(f"\rWpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): {deposit} {''}\b", end='',
                          flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                deposit += chr(key)
                print(chr(key), end='', flush=True)

    if deposit == '':
        deposit = "Brak"
        isDeposit = False
    else:
        deposit = str(deposit) + "zl"
        isDeposit = True

    if isJson:
        newData = []
        i = 1
        for entry in temp:
            if i == int(documentChoice):
                entry["deposit"] = deposit
                if isDeposit:
                    rentalDateSTR = entry["rentalDate"]
                    rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat)
                    maxReturnDate = rentalDate + datetime.timedelta(weeks=2)
                    entry["maxDate"] = str(f"{maxReturnDate.strftime(dateFormat)}")
                else:
                    entry["maxDate"] = '14:10'
                newData.append(entry)
                i = i + 1
            else:
                newData.append(entry)
                i = i + 1

        with open(activeHiresFile, 'w') as f:
            json.dump(newData, f, indent=4)
        print('Zmieniono kaucję')
    else:
        try:
            chosenDocument = activeCollection.find_one({'_id': documentIDs[int(documentChoice) - 1]["_id"]})
            if isDeposit:
                rentalDateSTR = chosenDocument["rentalDate"]
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat)
                maxReturnDate = rentalDate + datetime.timedelta(weeks=2)
                maxDate = str(f"{maxReturnDate.strftime(dateFormat)}")
            else:
                maxDate = '14:10'
            updates = {
                "$set": {"deposit": deposit, "maxDate": maxDate}
            }
            activeCollection.update_one({"_id": chosenDocument["_id"]}, update=updates)
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        else:
            print(f'{Fore.GREEN}Zmieniono kaucję{Style.RESET_ALL}')


def viewTodayReturns():
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja', 'Status'])
    results.title = 'Książki z dzisiejszym terminem'
    with open(activeHiresFile, 'r') as f:
        jsonFile = json.load(f)

    if isJson:
        for entry in jsonFile:
            maxReturnDate = ''
            name = entry["name"]
            lastName = entry["lastName"]
            rentClass = entry["klasa"]
            bookTitle = entry["bookTitle"]
            rentalDate = entry["rentalDate"]
            maxDateSTR = entry["maxDate"]
            deposit = entry["deposit"]
            overdue = ''
            maxDate = None

            # overdue
            today = None
            # jeśli kaucja jest wpłacona
            today = datetime.datetime.today().date()
            maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
            if maxDate < today:
                difference = today - maxDate
                overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
            else:
                overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            today = datetime.date.today().strftime(dateFormat)
            if maxDateSTR != '14:10':
                maxReturnDate = datetime.datetime.strptime(maxDateSTR, dateFormat).strftime(dateFormat)

            if maxReturnDate <= today or maxDateSTR == '14:10':
                results.add_row(
                    [name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDateSTR), deposit, overdue])
    else:
        try:
            entries = activeCollection.find()
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        for entry in entries:
            name = entry["name"]
            lastName = entry["lastName"]
            rentClass = entry["klasa"]
            bookTitle = entry["bookTitle"]
            rentalDateSTR = entry["rentalDate"]
            maxDateSTR = entry["maxDate"]
            deposit = entry["deposit"]
            # overdue
            overdue = ''
            maxDate = None
            today = datetime.datetime.today().date()
            if maxDateSTR != '14:10':
                # jeśli kaucja jest wpłacona
                isDeposit = True
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
            else:
                # jeśli kaucja nie została wpłacona
                isDeposit = False
                rentalDate = datetime.datetime.strptime(rentalDateSTR, dateFormat).date()
                if rentalDate < today:
                    difference = today - rentalDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            if isDeposit and maxDate <= today or not isDeposit:
                results.add_row(
                    [name, lastName, rentClass, bookTitle, rentalDateSTR, maxDateSTR, deposit,
                     overdue])

    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)


def extension():
    with open(activeHiresFile, 'r') as f:
        temp = json.load(f)
        dataLengthList = []
        if isJson:
            for item in temp:
                if item["maxDate"] != '14:10':
                    dataLengthList.append(item)
            dataLength = len(dataLengthList)
        else:
            try:
                dataLength = activeCollection.count_documents({"maxDate": {"$not": {"$eq": "14:10"}}})
                entries = activeCollection.find({"maxDate": {"$not": {"$eq": "14:10"}}})
            except Exception as error:
                print(Fore.RED + str(error) + Style.RESET_ALL)

    # View
    view = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja', 'Status'])
    view.title = 'Trwające wypożyczenia'
    if isJson:
        newData = []
        for item in temp:
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]
            overdue = ''
            maxDate = None

            # overdue
            today = None
            if maxDateSTR != '14:10':
                # jeśli kaucja jest wpłacona
                today = datetime.datetime.today().date()
                maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
                if maxDate < today:
                    difference = today - maxDate
                    overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
                else:
                    overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'
                view.add_row(
                    [name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
    else:
        documentIDs = []
        for item in entries:
            name = item["name"]
            lastName = item["lastName"]
            rentClass = item["klasa"]
            bookTitle = item["bookTitle"]
            rentalDateSTR = item["rentalDate"]
            maxDateSTR = item["maxDate"]
            deposit = item["deposit"]
            overdue = ''
            maxDate = None

            # overdue
            today = None
            # jeśli kaucja jest wpłacona
            today = datetime.datetime.today().date()
            maxDate = datetime.datetime.strptime(maxDateSTR, dateFormat).date()
            if maxDate < today:
                difference = today - maxDate
                overdue = f'{Style.BRIGHT}{Fore.RED}Przetrzymanie (Kara: {difference.days}zł){Style.RESET_ALL}'
            else:
                overdue = f'{Fore.GREEN}Wypożyczona{Style.RESET_ALL}'

            view.add_row([name, lastName, rentClass, bookTitle, str(rentalDateSTR), str(maxDateSTR), deposit, overdue])
            documentIDs.append(item)

    view.add_autoindex('ID')
    if len(view.rows) <= 0:
        print()
        print('Lista jest pusta')
        return
    else:
        print(view)
    # End of view

    print("Wpisz ID wypożyczenia które chcesz przedłużyć: ", end='',
          flush=True)  # use print instead of input to avoid blocking
    documentChoice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                idRange = range(1, int(dataLength + 1))
                if int(documentChoice) in idRange:
                    print()
                    break  # exit loop
                else:
                    continue
            elif key == 8:  # backspace key
                if len(documentChoice) > 0:
                    documentChoice = documentChoice[:-1]
                    print(f"\rWpisz ID wypożyczenia które chcesz przedłużyć: {documentChoice} {''}\b", end='',
                          flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                documentChoice += chr(key)
                print(chr(key), end='', flush=True)

    if isJson:
        i = 1
        for entry in temp:
            if entry["maxDate"] != '14:10':
                if i == int(documentChoice):
                    maxDate = datetime.datetime.strptime(entry["maxDate"], dateFormat)
                    maxDate = maxDate + datetime.timedelta(weeks=2)
                    entry["maxDate"] = maxDate.strftime(dateFormat)
                    newData.append(entry)
                    i = i + 1
                else:
                    newData.append(entry)
                    i = i + 1
            else:
                newData.append(entry)

        with open(activeHiresFile, 'w') as f:
            json.dump(newData, f, indent=4)
        print('Przedłużono wypożyczenie')
    else:
        try:
            maxDate = ''
            chosenDocument = activeCollection.find_one({'_id': documentIDs[int(documentChoice) - 1]["_id"]})
            maxDate = datetime.datetime.strptime(chosenDocument["maxDate"], dateFormat)
            maxDate = maxDate + datetime.timedelta(weeks=2)
            updates = {
                "$set": {"maxDate": maxDate.strftime(dateFormat)}
            }
            activeCollection.update_one({"_id": chosenDocument["_id"]}, update=updates)
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        else:
            print(f'{Fore.GREEN}Przedłużono wypożyczenie{Style.RESET_ALL}')

            
def modifying():
    if isJson:
        with open(activeHiresFile, "r") as f:
            viewActiveHires()
            temp = json.load(f)
            data_length = len(temp)
    else:
        documentIDs = viewActiveHires()
        try:
            data_length = activeCollection.count_documents({})
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)

    if data_length <= 0:
        return

    print("Wpisz ID wypożyczenia w którym chcesz dodać kaucję: ", end='',
          flush=True)  # use print instead of input to avoid blocking
    documentChoice = ""
    while True:
        if msvcrt.kbhit():
            key = ord(msvcrt.getch())
            if key == 27:  # escape key
                print()
                os.system('cls')
                return  # exit function
            elif key == 13:  # enter key
                idRange = range(1, int(data_length + 1))
                if int(documentChoice) in idRange:
                    print()
                    break  # exit loop
            elif key == 8:  # backspace key
                if len(documentChoice) > 0:
                    documentChoice = documentChoice[:-1]
                    print(f"\rWpisz ID wypożyczenia w którym chcesz dodać kaucję: {documentChoice} {''}\b", end='',
                          flush=True)
            elif key == 224:  # special keys (arrows, function keys, etc.)
                key = ord(msvcrt.getch())
                if key == 72:  # up arrow key
                    continue
                elif key == 80:  # down arrow key
                    continue
                elif key == 75:  # left arrow key
                    continue
                elif key == 77:  # right arrow key
                    continue
            else:
                documentChoice += chr(key)
                print(chr(key), end='', flush=True)

    if isJson:
        newData = []
        i = 1
        for entry in temp:
            if i == int(documentChoice):
                print("Zmień imię: ", end='', flush=True)  # use print instead of input to avoid blocking
                name = entry["name"]
                print(f"\rZmień imię: {name} {''}\b", end='', flush=True)
                while True:
                    if msvcrt.kbhit():
                        key = ord(msvcrt.getch())
                        if key == 27:  # escape key
                            print()
                            os.system('cls')
                            return  # exit function
                        elif key == 13:  # enter key
                            print()
                            break  # exit loop
                        elif key == 8:  # backspace key
                            if len(name) > 0:
                                name = name[:-1]
                                print(f"\rZmień imię: {name} {''}\b", end='', flush=True)
                        elif key == 224:  # special keys (arrows, function keys, etc.)
                            key = ord(msvcrt.getch())
                            if key == 72:  # up arrow key
                                continue
                            elif key == 80:  # down arrow key
                                continue
                            elif key == 75:  # left arrow key
                                continue
                            elif key == 77:  # right arrow key
                                continue
                        else:
                            name += chr(key)
                            print(chr(key), end='', flush=True)

                print("Zmień nazwisko: ", end='', flush=True)  # use print instead of input to avoid blocking
                lastName = entry['lastName']
                print(f"\rZmień nazwisko: {lastName} {''}\b", end='', flush=True)
                while True:
                    if msvcrt.kbhit():
                        key = ord(msvcrt.getch())
                        if key == 27:  # escape key
                            print()
                            os.system('cls')
                            return  # exit function
                        elif key == 13:  # enter key
                            print()
                            break  # exit loop
                        elif key == 8:  # backspace key
                            if len(lastName) > 0:
                                lastName = lastName[:-1]
                                print(f"\rZmień nazwisko: {lastName} {''}\b", end='', flush=True)
                        elif key == 224:  # special keys (arrows, function keys, etc.)
                            key = ord(msvcrt.getch())
                            if key == 72:  # up arrow key
                                continue
                            elif key == 80:  # down arrow key
                                continue
                            elif key == 75:  # left arrow key
                                continue
                            elif key == 77:  # right arrow key
                                continue
                        else:
                            lastName += chr(key)
                            print(chr(key), end='', flush=True)

                print("Zmień klasę: ", end='', flush=True)  # use print instead of input to avoid blocking
                klasa = entry['klasa']
                print(f"\rZmień klasę: {klasa} {''}\b", end='', flush=True)
                while True:
                    if msvcrt.kbhit():
                        key = ord(msvcrt.getch())
                        if key == 27:  # escape key
                            print()
                            os.system('cls')
                            return  # exit function
                        elif key == 13:  # enter key
                            print()
                            break  # exit loop
                        elif key == 8:  # backspace key
                            if len(klasa) > 0:
                                klasa = klasa[:-1]
                                print(f"\rZmień klasę: {klasa} {''}\b", end='', flush=True)
                        elif key == 224:  # special keys (arrows, function keys, etc.)
                            key = ord(msvcrt.getch())
                            if key == 72:  # up arrow key
                                continue
                            elif key == 80:  # down arrow key
                                continue
                            elif key == 75:  # left arrow key
                                continue
                            elif key == 77:  # right arrow key
                                continue
                        else:
                            klasa += chr(key)
                            print(chr(key), end='', flush=True)

                print("Zmień tytuł książki: ", end='', flush=True)  # use print instead of input to avoid blocking
                bookTitle = entry['bookTitle']
                print(f"\rZmień tytuł książki: {bookTitle} {''}\b", end='', flush=True)
                while True:
                    if msvcrt.kbhit():
                        key = ord(msvcrt.getch())
                        if key == 27:  # escape key
                            print()
                            os.system('cls')
                            return  # exit function
                        elif key == 13:  # enter key
                            print()
                            break  # exit loop
                        elif key == 8:  # backspace key
                            if len(bookTitle) > 0:
                                bookTitle = bookTitle[:-1]
                                print(f"\rZmień tytuł książki: {bookTitle} {''}\b", end='', flush=True)
                        elif key == 224:  # special keys (arrows, function keys, etc.)
                            key = ord(msvcrt.getch())
                            if key == 72:  # up arrow key
                                continue
                            elif key == 80:  # down arrow key
                                continue
                            elif key == 75:  # left arrow key
                                continue
                            elif key == 77:  # right arrow key
                                continue
                        else:
                            bookTitle += chr(key)
                            print(chr(key), end='', flush=True)
                entry['name'] = name
                entry['lastName'] = lastName
                entry['klasa'] = klasa
                entry['bookTitle'] = bookTitle
                newData.append(entry)
                i = i + 1
            else:
                newData.append(entry)
                i = i + 1

        with open(activeHiresFile, 'w') as f:
            json.dump(newData, f, indent=4)
        print('Zmieniono kaucję')
    else:
        try:
            chosenDocument = activeCollection.find_one({'_id': documentIDs[int(documentChoice) - 1]["_id"]})
            print("Zmień imię: ", end='', flush=True)  # use print instead of input to avoid blocking
            name = chosenDocument["name"]
            print(f"\rZmień imię: {name} {''}\b", end='', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = ord(msvcrt.getch())
                    if key == 27:  # escape key
                        print()
                        os.system('cls')
                        return  # exit function
                    elif key == 13:  # enter key
                        print()
                        break  # exit loop
                    elif key == 8:  # backspace key
                        if len(name) > 0:
                            name = name[:-1]
                            print(f"\rZmień imię: {name} {''}\b", end='', flush=True)
                    elif key == 224:  # special keys (arrows, function keys, etc.)
                        key = ord(msvcrt.getch())
                        if key == 72:  # up arrow key
                            continue
                        elif key == 80:  # down arrow key
                            continue
                        elif key == 75:  # left arrow key
                            continue
                        elif key == 77:  # right arrow key
                            continue
                    else:
                        name += chr(key)
                        print(chr(key), end='', flush=True)

            print("Zmień nazwisko: ", end='', flush=True)  # use print instead of input to avoid blocking
            lastName = chosenDocument['lastName']
            print(f"\rZmień nazwisko: {lastName} {''}\b", end='', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = ord(msvcrt.getch())
                    if key == 27:  # escape key
                        print()
                        os.system('cls')
                        return  # exit function
                    elif key == 13:  # enter key
                        print()
                        break  # exit loop
                    elif key == 8:  # backspace key
                        if len(lastName) > 0:
                            lastName = lastName[:-1]
                            print(f"\rZmień nazwisko: {lastName} {''}\b", end='', flush=True)
                    elif key == 224:  # special keys (arrows, function keys, etc.)
                        key = ord(msvcrt.getch())
                        if key == 72:  # up arrow key
                            continue
                        elif key == 80:  # down arrow key
                            continue
                        elif key == 75:  # left arrow key
                            continue
                        elif key == 77:  # right arrow key
                            continue
                    else:
                        lastName += chr(key)
                        print(chr(key), end='', flush=True)

            print("Zmień klasę: ", end='', flush=True)  # use print instead of input to avoid blocking
            klasa = chosenDocument['klasa']
            print(f"\rZmień klasę: {klasa} {''}\b", end='', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = ord(msvcrt.getch())
                    if key == 27:  # escape key
                        print()
                        os.system('cls')
                        return  # exit function
                    elif key == 13:  # enter key
                        print()
                        break  # exit loop
                    elif key == 8:  # backspace key
                        if len(klasa) > 0:
                            klasa = klasa[:-1]
                            print(f"\rZmień klasę: {klasa} {''}\b", end='', flush=True)
                    elif key == 224:  # special keys (arrows, function keys, etc.)
                        key = ord(msvcrt.getch())
                        if key == 72:  # up arrow key
                            continue
                        elif key == 80:  # down arrow key
                            continue
                        elif key == 75:  # left arrow key
                            continue
                        elif key == 77:  # right arrow key
                            continue
                    else:
                        klasa += chr(key)
                        print(chr(key), end='', flush=True)

            print("Zmień tytuł książki: ", end='', flush=True)  # use print instead of input to avoid blocking
            bookTitle = chosenDocument['bookTitle']
            print(f"\rZmień tytuł książki: {bookTitle} {''}\b", end='', flush=True)
            while True:
                if msvcrt.kbhit():
                    key = ord(msvcrt.getch())
                    if key == 27:  # escape key
                        print()
                        os.system('cls')
                        return  # exit function
                    elif key == 13:  # enter key
                        print()
                        break  # exit loop
                    elif key == 8:  # backspace key
                        if len(bookTitle) > 0:
                            bookTitle = bookTitle[:-1]
                            print(f"\rZmień tytuł książki: {bookTitle} {''}\b", end='', flush=True)
                    elif key == 224:  # special keys (arrows, function keys, etc.)
                        key = ord(msvcrt.getch())
                        if key == 72:  # up arrow key
                            continue
                        elif key == 80:  # down arrow key
                            continue
                        elif key == 75:  # left arrow key
                            continue
                        elif key == 77:  # right arrow key
                            continue
                    else:
                        bookTitle += chr(key)
                        print(chr(key), end='', flush=True)
            updates = {
                "$set": {"name": name, "lastName":lastName,"klasa":klasa, "bookTitle":bookTitle}
            }
            activeCollection.update_one({"_id": chosenDocument["_id"]}, update=updates)
        except Exception as error:
            print(Fore.RED + str(error) + Style.RESET_ALL)
        else:
            print(f'{Fore.GREEN}Zmodyfikowano wypożyczenie{Style.RESET_ALL}')


def onExit():
    global keycloak_openid
    global token
    global passwordsDBconnection
    global passwordsDBcursor
    keycloak_openid.logout(token["refresh_token"])
    passwordsDBcursor.close()
    passwordsDBconnection.close()

adminTools = AdminTools(senderEmail, receiveEmail, senderPassword)
mongoPreconfiguration()
profiles()
atexit.register(onExit)
while True:
    choice = 0
    print()
    if isJson:
        print(f'{Fore.LIGHTWHITE_EX}Zalogowano jako {Fore.LIGHTGREEN_EX}{profileUsername}{Style.RESET_ALL}- Tryb lokalny{Style.RESET_ALL}')
    else:
        print(f"{Fore.LIGHTWHITE_EX}ZALOGOWANO JAKO {Fore.LIGHTGREEN_EX}{profileUsername}{Fore.LIGHTWHITE_EX} - Tryb MongoDB{Style.RESET_ALL}")
    print("----------------------------------------------------------------------------")
    print("[1] - Dodaj wypożyczenie")
    print("[2] - Zakończ wypożyczenie")
    print("[3] - Wypożyczone książki")
    print("[4] - Zarządzaj wypożyczeniami")
    print("[5] - Wyświetl książki z dzisiejszą datą zwrotu")
    print("'cp' - Zmień hasło do profilu")

    choice = input("Wybierz z listy: ")
    print()
    if choice == '1':
        isTokenActive = keycloak_openid.introspect(token['access_token'])
        if isTokenActive['active']:
            if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                addHire()
                token = keycloak_openid.refresh_token(token['refresh_token'])
            else:
                print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
        else:
            os.system('cls')
            print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
            profiles()
    elif choice == '2':
        isTokenActive = keycloak_openid.introspect(token['access_token'])
        if isTokenActive['active']:
            if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                endHire()
                token = keycloak_openid.refresh_token(token['refresh_token'])
            else:
                print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
        else:
            os.system('cls')
            print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
            profiles()
    elif choice == '3':
        print('[1] - Wyświetl trwające wypożyczenia')
        print('[2] - Wyświetl historię wypożyczeń')
        print('[3] - Przeszukaj trwające wypożyczenia')
        print('[4] - Przeszukaj historię wypożyczeń')
        choice = input("Wybierz z listy: ")
        print()
        if choice == '1':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=viewerRole, username=profileUsername):
                    viewActiveHires()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        elif choice == '2':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=viewerRole, username=profileUsername):
                    viewHistoryHires()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        elif choice == '3':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=viewerRole, username=profileUsername):
                    activeSearch()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        elif choice == '4':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=viewerRole, username=profileUsername):
                    historySearch()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        else:
            print(f"{Fore.RED}Nie znaleziono takiej komendy. Spróbuj ponownie.{Style.RESET_ALL}")
    elif choice == "4":
        print('[1] - Zmień lub dodaj kaucję')
        print('[2] - Przedłuż wypożyczenie')
        print('[3] - Zmodyfikuj wypożyczenie')
        choice = input("Wybierz z listy: ")
        print()
        if choice == '1':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                    addDeposit()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        elif choice == '2':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                    extension()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        elif choice == '3':
            isTokenActive = keycloak_openid.introspect(token['access_token'])
            if isTokenActive['active']:
                if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                    modifying()
                    token = keycloak_openid.refresh_token(token['refresh_token'])
                else:
                    print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
            else:
                os.system('cls')
                print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
                profiles()
        else:
            print(f"{Fore.RED}Nie znaleziono takiej komendy. Spróbuj ponownie.{Style.RESET_ALL}")
    elif choice == '5':
        isTokenActive = keycloak_openid.introspect(token['access_token'])
        if isTokenActive['active']:
            if adminTools.checkRole(roleName=librarianRole, username=profileUsername):
                viewTodayReturns()
                token = keycloak_openid.refresh_token(token['refresh_token'])
            else:
                print(f'{Fore.RED}Nie masz uprawnień do tej funkcji{Style.RESET_ALL}')
        else:
            os.system('cls')
            print(f'{Fore.RED}Twoja sesja wygasła.{Style.RESET_ALL}')
            profiles()
    elif choice == 'cls':
        os.system('cls')
    elif choice == 'cfg mongo':
        os.system('cls')
        set_key(find_dotenv(), "MONGODB_USER", 'None')
        set_key(find_dotenv(), "MONGODB_PASSWORD", 'None')
        mongoPreconfiguration()
    elif choice == 'cfg admin':
        os.system('cls')
        print(f"[1] - Change mode - current: {Fore.LIGHTBLUE_EX}{get_key(find_dotenv(), 'JSON')}{Style.RESET_ALL}")
        print("[2] - Reset active rents list")
        print("[3] - Reset history")
        print("[4] - Reset all")
        print("[5] - Add profile")
        print("[6] - Delete profile")
        print("[7] - Modify profile")
        print("[8] - Change admin Password")
        choice = input("Wybierz z listy: ")
        if choice == '1':
            adminTools.changeMode()
        elif choice == '2':
            adminTools.resetActive()
        elif choice == '3':
            adminTools.resetHistory()
        elif choice == '4':
            adminTools.resetAll()
        elif choice == '5':
            adminTools.addProfile()
        elif choice == '6':
            adminTools.deleteProfile()
        elif choice == '7':
            adminTools.modifyProfile()
        elif choice == '8':
            adminTools.changeAdminPassword()
        else:
            print(f"{Fore.RED}Nie znaleziono takiej komendy. Spróbuj ponownie.{Style.RESET_ALL}")
    elif choice == 'logout':
        os.system('cls')
        keycloak_openid.logout(token["refresh_token"])
        profiles()
    elif choice == 'cp':
        adminTools.changePassword(profileUsername)
    else:
        print(f"{Fore.RED}Nie znaleziono takiej komendy. Spróbuj ponownie.{Style.RESET_ALL}")