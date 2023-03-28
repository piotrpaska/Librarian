import json
import datetime
import prettytable

activeHiresFile = 'active.json'
historyFile = 'history.json'
dateFormat = "%d.%m.%Y"

def addHire():
    """Zapisywane dane to: imię, nazwisko, klasa, tytuł książki, data wypożyczenia, kaucja"""
    sure = 0
    hireData = {}

    # imię
    hireData["name"] = input("Wpisz imię: ")

    # nazwisko
    hireData["lastName"] = input("Wpisz nazwisko: ")

    hireData["class"] = input("Podaj klasę czytelnika (np. 2a): ")

    # tytuł książki
    hireData["bookTitle"] = input("Wpisz tytuł wypożyczonej książki: ")

    deposit = input("Wpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): ")
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

    summary = prettytable.PrettyTable(['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja'])
    summary.add_row([hireData["name"], hireData["lastName"], hireData["class"], hireData["bookTitle"], hireData["rentalDate"], hireData["maxDate"], hireData["deposit"]])
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
            print("Wprowadzone dane są niepoprawne. Spróbuj ponownie")
            continue

    if sure == 1:
        try:
            with open(activeHiresFile, "r") as f:
                temp = json.load(f)
                temp.append(hireData)
            with open(activeHiresFile, "w") as f:
                json.dump(temp, f, indent=4)
            print("Wypożyczenie dodane")
        except Exception as error:
            print(error)
    elif sure == 0:
        print("Anulowano dodanie wypożyczenia")

def endHire():
    viewActiveHires()
    new_data = []

    with open(activeHiresFile, "r") as f:
        temp = json.load(f)
        data_length = len(temp)

    while True:
        try:
            print("Aby wybrać wypożyczenie które chcesz zakończyć wpisz ID tego wypożyczenia")
            deleteOption = input(f"Wybierz ID 1-{data_length}: ")
            delOptRange = range(1, int(data_length + 1))
            if int(deleteOption) in delOptRange:
                print("Wypożyczenie zakończone")
                break
            else:
                print("Wprowadzone dane są niepoprawne. Spróbuj ponownie")
        except Exception:
            print("To nie jest liczba")

    i = 1
    for entry in temp:
        if i == int(deleteOption):
            returnDate = datetime.datetime.now()
            entry["returnDate"] = str(f"{returnDate.day}.{returnDate.month}.{returnDate.year} - {returnDate.hour}:{returnDate.minute}")
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

def viewActiveHires():
    with open(activeHiresFile, 'r') as f:
        jsonFile = json.load(f)
    results = prettytable.PrettyTable(['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja'])
    results.title = 'Trwające wypożyczenia'
    for item in jsonFile:
        name = item["name"]
        lastName = item["lastName"]
        rentClass = item["class"]
        bookTitle = item["bookTitle"]
        rentalDate = item["rentalDate"]
        maxDate = item["maxDate"]
        deposit = item["deposit"]
        results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), deposit])
    results.add_autoindex('ID')
    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)

def viewHistoryHires():
    with open(historyFile, 'r') as f:
        jsonFile = json.load(f)
    results = prettytable.PrettyTable(
        ['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Data zwrotu', 'Kaucja'])
    results.title = 'Historia wypożyczeń'
    for item in jsonFile:
        name = item["name"]
        lastName = item["lastName"]
        rentClass = item["class"]
        bookTitle = item["bookTitle"]
        rentalDate = item["rentalDate"]
        maxDate = item["maxDate"]
        returnDate = item["returnDate"]
        deposit = item["deposit"]
        results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate),str(returnDate), deposit])
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

    while True:
        try:
            choice = int(input('Po czym chcesz szukać: '))
            if choice not in range(1, 4):
                raise Exception
            break
        except Exception:
            print('Wprowadzone dane są niepoprawne. Spróbuj ponownie')
            continue

    phrase = input('Wprowadź szukaną frazę: ')
    results = prettytable.PrettyTable(['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja'])
    results.title = f'Szukana fraza: {phrase}'
    with open(activeHiresFile, 'r') as f:
        jsonFile = json.load(f)
    for item in jsonFile:

        name = item["name"]
        lastName = item["lastName"]
        rentClass = item["class"]
        bookTitle = item["bookTitle"]
        rentalDate = item["rentalDate"]
        maxDate = item["maxDate"]
        deposit = item["deposit"]

        if choice == 1:
            if str(phrase) in name:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), deposit])
        if choice == 2:
            if str(phrase) in lastName:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), deposit])
        if choice == 3:
            if str(phrase) in rentClass:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), deposit])
        if choice == 4:
            if str(phrase) in bookTitle:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate), deposit])

    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)

def historySearch():
    print('[1] - imię')
    print('[2] - nazwisko')
    print('[3] - klasa')
    print('[4] - tytuł książki')

    while True:
        try:
            choice = int(input('Po czym chcesz szukać: '))
            if choice not in range(1, 4):
                raise Exception
            break
        except Exception:
            print('Wprowadzone dane są niepoprawne. Spróbuj ponownie')
            continue

    phrase = input('Wprowadź szukaną frazę: ')
    results = prettytable.PrettyTable(['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Data zwrotu', 'Kaucja'])
    results.title = f'Szukana fraza: {phrase}'
    with open(historyFile, 'r') as f:
        jsonFile = json.load(f)
    for item in jsonFile:

        name = item["name"]
        lastName = item["lastName"]
        rentClass = item["class"]
        bookTitle = item["bookTitle"]
        rentalDate = item["rentalDate"]
        maxDate = item["maxDate"]
        returnDate = item['returnDate']
        deposit = item["deposit"]

        if choice == 1:
            if str(phrase) in name:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate),str(returnDate), deposit])
        if choice == 2:
            if str(phrase) in lastName:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate),str(returnDate), deposit])
        if choice == 3:
            if str(phrase) in rentClass:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate),str(returnDate), deposit])
        if choice == 4:
            if str(phrase) in bookTitle:
                results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDate),str(returnDate), deposit])

    if len(results.rows) == 0:
        print()
        print('Lista jest pusta')
    else:
        print(results)

def addDeposit():
    viewActiveHires()
    newData = []
    with open(activeHiresFile, 'r') as f:
        temp = json.load(f)
        dataLenght = len(temp)

    while True:
        objectChange = int(input('Wpisz ID wypożyczenia w którym chcesz dodać kaucję: '))
        idRange = range(1, int(dataLenght + 1))
        if int(objectChange) in idRange:
            deposit = input("Wpisz wartość kaucji (jeśli nie wpłacił kaucji kliknij ENTER): ")
            isDeposit = bool
            if deposit == '':
                deposit = 'Brak'
                isDeposit = False
            else:
                deposit = str(deposit) + "zl"
                isDeposit = True
            break
        else:
            print("Wprowadzone dane są niepoprawne. Spróbuj ponownie")

    i = 1
    for entry in temp:
        if i == objectChange:
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
        json.dump(newData,f, indent=4)

    print('Zmieniono kaucję')

def viewTodayReturns():
    results = prettytable.PrettyTable(['Imię', 'Nazwisko', 'Klasa', 'Tytuł książki', 'Data wypożyczenia', 'Zwrot do', 'Kaucja'])
    results.title = 'Książki z dzisiejszym terminem'
    with open(activeHiresFile, 'r') as f:
        jsonFile = json.load(f)

    for entry in jsonFile:
        maxReturnDate = ''
        name = entry["name"]
        lastName = entry["lastName"]
        rentClass = entry["class"]
        bookTitle = entry["bookTitle"]
        rentalDate = entry["rentalDate"]
        maxDateSTR = entry["maxDate"]
        deposit = entry["deposit"]

        today = datetime.date.today().strftime(dateFormat)
        if maxDateSTR != '14:10':
            maxReturnDate = datetime.datetime.strptime(maxDateSTR, dateFormat).strftime(dateFormat)

        print(today)
        print(maxReturnDate)

        if maxReturnDate == today or maxDateSTR == '14:10':
            results.add_row([name, lastName, rentClass, bookTitle, str(rentalDate), str(maxDateSTR), deposit])

    print(results)

while True:
    choice = 0
    print("----------------------------------------------------------------------------")
    print("[1] - Dodaj wypożyczoną książkę")
    print("[2] - Zakończ wypożyczenie")
    print("[3] - Zobacz listę wypożyczonych książek")
    print("[4] - Zobacz historię wypożyczeń")
    print("[5] - Przeszukaj aktywne wypożyczenie")
    print("[6] - Przeszukaj historię wypożyczeń")
    print("[7] - Dodaj lub zmień kaucję")
    print("[8] - Książki z dzisiejszym terminem zwrotu")
    try:
        choice = int(input("Wybierz z listy: "))
    except Exception:
        print("Wprowadzone dane są niepoprawne. Spróbuj ponownie")
    print()

    if choice == 1:
        addHire()
    elif choice == 2:
        endHire()
    elif choice == 3:
        viewActiveHires()
    elif choice == 4:
        viewHistoryHires()
    elif choice == 5:
        activeSearch()
    elif choice == 6:
        historySearch()
    elif choice == 7:
        addDeposit()
    elif choice == 8:
        viewTodayReturns()
    else:
        print("Wprowadzone dane są niepoprawne. Spróbuj ponownie")
