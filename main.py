# pip install dnspython
# pip install pymongo[srv]
# pip install colorama
# pip install pandas

import os
from pymongo import MongoClient
import re
import pandas as pd


class Fore:
    LIGHTGREEN_EX = ''
    LIGHTBLUE_EX = ''
    GREEN = ''
    RED = ''
    YELLOW = ''
    CYAN = ''


class Style:
    RESET_ALL = ''


try:
    from colorama import Fore, Style
    pass
except:
    print("colorama import failed")


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    return False


DB_COLLECTION = ''
FIELDS = ['Name', 'Ph_number', 'Email']


def db_init():
    fileName = "db_link.txt"
    db_link = ''
    try:
        file = open(fileName, "r")
        db_link = file.read()
        file.close()
    except:
        pass
    link_exists = bool(db_link)
    if not link_exists:
        db_link = input("enter mongodb connection url: ")
        file = open(fileName, "w")
        file.write(db_link)
        file.close()
    client = ''
    try:
        client = MongoClient(db_link)
        db = client.phone_book
        return db.book
    except Exception as e:
        print("db connection failed")
        raise Exception(e)


def db_operation(db_collection, operation='r', condition={}, data={}, fields={}):
    try:
        switch = {
            'c': lambda: db_collection.count_documents(condition),
            'r': lambda: db_collection.find(condition, fields).sort("Name"),
            'w': lambda: db_collection.insert_one(data),
            'd': lambda: db_collection.delete_one(condition)
        }
        response = switch[operation]()
        return response
    except Exception as e:
        switch = {
            'c': 0,
            'r': {},
            'w': {},
            'd': False,
        }
        print("Error during:", operation, e)
        return switch[operation]


def pretty_print_statement(string, line='.', length=6, color=''):
    print(f"\n{color}{line*length}{string}{line*length}\n{Style.RESET_ALL}")


def validate(type, test_string):
    switch = {
        "Name": re.compile(r"^[A-Za-z]{3,15}\d+?$"),
        "Ph_number": re.compile(r"^\+?[0-9]{6,12}$"),
        "Email": re.compile(r"^\w{3,7}@\w{3,10}.\w{1,5}$")
    }
    return bool(re.fullmatch(switch[type], test_string))


def search_helper(search_string=''):
    search_query = {}
    if search_string:
        regex = {'$regex': f'^{search_string}'}
        fields = FIELDS
        search_query = {'$or': [{field: regex}
                                for field in fields]}
    view_fields = {field: 1 for field in FIELDS}
    view_fields["_id"] = 0
    contacts = db_operation(
        DB_COLLECTION, condition=search_query, fields=view_fields)
    contacts_ = []
    for contact in contacts:
        contacts_.append(contact)
    return contacts_


def save():
    name = input("enter name: ").strip()
    ph_number = input("enter ph.number: ").strip()
    email = input("enter email: ").strip()
    name_duplicate = db_operation(
        DB_COLLECTION, operation='c', condition={"Name": name}) > 0
    ph_number_duplicate = db_operation(
        DB_COLLECTION, operation='c', condition={"Ph_number": ph_number}) > 0
    email_duplicate = db_operation(
        DB_COLLECTION, operation='c', condition={"Email": email}) > 0
    if not validate("Name", name) or name_duplicate:
        pretty_print_statement("Username Duplicate/Invalid!", color=Fore.RED)
        return False
    elif not validate("Ph_number", ph_number) or ph_number_duplicate:
        pretty_print_statement(
            "Phone Number Duplicate/Invalid!", color=Fore.RED)
        return False
    elif not validate("Email", email) or email_duplicate:
        pretty_print_statement("Email Duplicate/Invalid!", color=Fore.RED)
        return False
    selected = input("Confirm details?(y/n): ").strip().lower()
    if selected == 'y':
        contact = {"Name": name, "Ph_number": ph_number, "Email": email}
        pretty_print_statement("Saving...",
                               color=Fore.YELLOW)
        db_operation(DB_COLLECTION, 'w', data=dict(contact))
        pretty_print_statement("Saved!",
                               color=Fore.LIGHTGREEN_EX)
        pretty_print_dict(contact)
        return True
    return False


def pretty_print_dict(dict):
    string = '-'*25+'\n'
    for key in list(dict.keys()):
        spaces = max(14 - len(key), 1)
        string += f"{key}{' '*spaces}: {dict[key]}\n"
    string += '='*25
    print(f'{Fore.LIGHTBLUE_EX}{string}{Style.RESET_ALL}')


def display_contacts(contacts):
    if len(contacts):
        i = 1
        for contact in contacts:
            print(f"{Fore.CYAN}SL no.: {str(i)}{Style.RESET_ALL}")
            pretty_print_dict(contact)
            response = input(
                "--press any key to continue or q to quit--"
            ).strip().lower()
            i += 1
            if response == 'q':
                break
    else:
        pretty_print_statement("No Contacts Available!",
                               color=Fore.LIGHTYELLOW_EX)
    pretty_print_statement("END", '-', 11, color=Fore.YELLOW)


def search():
    search_string = input("enter name/number/email: ").strip()
    contacts = search_helper(search_string)
    display_contacts(contacts)
    return True


def diaplay_all_contacts():
    contacts = search_helper()
    response = input("display as data frame? (y/n): ")
    if response == 'y':
        print(pd.DataFrame(contacts))
    else:
        display_contacts(contacts)


def delete():
    search_string = input("enter name/number/email: ").strip()
    contacts = search_helper(search_string)
    if len(contacts):
        pretty_print_dict(contacts[0])
        selected = input("Confirm Delete?(y/n): ").lower()
        if selected == 'y':
            db_operation(DB_COLLECTION, 'd', condition=contacts[0])
            pretty_print_statement("Deleted!", color=Fore.LIGHTYELLOW_EX)
            return True
    else:
        pretty_print_statement(
            "Contact Not Found!", color=Fore.RED)
    return False


def quit():
    pretty_print_statement("Quitting!", '*', 8, color=Fore.YELLOW)
    return True


states = {  # Emulate frontend using cli
    1: {
        'query':
        lambda: input(
            "create/search/delete/display_all? (c/s/d/disp),(q/cls): ")
            .strip().lower(),
        'functions': {
            'c': {'f': save, 's': 1},
            's': {'f': search, 's': 1},
            'd': {'f': delete, 's': 1},
            'disp': {'f': diaplay_all_contacts, 's': 1},
            'cls': {'f': clear_terminal, 's': 1},
            'q': {'f': quit, 's': 0},
        }
    },
}


def state_manager(state):
    state_obj = states[state]
    response = state_obj['query']()
    if response in state_obj['functions']:
        success = False
        success = state_obj['functions'][response]['f']()
        if success:
            state = state_obj['functions'][response]['s']
    return state


def main():
    # innit db
    global DB_COLLECTION
    DB_COLLECTION = db_init()
    pretty_print_statement(
        "Phone Book (use cls to clear and q to quit)", '*', 10, Fore.GREEN)
    state = 1
    while state:
        state = state_manager(state)


main()  # Execution starts here
