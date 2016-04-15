__author__ = 'Nathalie'

import sqlite3
from requests import Session, Request, exceptions
from requester import connect_to_uz, exec_request, RequestError, UZ_URI_BASE
from os import path
from json import loads
from string import ascii_lowercase


DB_BASE_NAME = 'cities.sqlite'
# LANGS = {'ua': 'ає', 'en': 'ax', 'ru': 'аэ'}
LANGS = {'ua': 'абвгдеєжзиіїйклмнопрстуфхцчшщьюя', 'en': ascii_lowercase,
'ru': 'абвгдежзийклмнопрстуфхцчшщьъэюя'}
STATION_SEARCH = 'purchase/station/'


def retrieve_cities(l, l_set):
    l_url = '' if l == 'ua' else l + '/'
    db_name = l + '_' + DB_BASE_NAME
    if path.isfile(db_name):
        upd = input(l + ' database already exists. Update it? (Yes | Any-key): ')
        if upd.lower() != 'yes':
            return

    conn = sqlite3.connect(db_name)
    conn.executescript('''
        DROP TABLE IF EXISTS City;

        CREATE TABLE City(
          cname TEXT NOT NULL UNIQUE,
          ccode TEXT NOT NULL
        )

        ''')
    conn.commit()

    res = {}
    with Session() as s:
        try:
            connect_to_uz(s)
            for char_1 in l_set:
                for char_2 in l_set:
                    print(char_1 + char_2)
                    cities_req_url = UZ_URI_BASE + l_url + STATION_SEARCH + char_1 + char_2
                    cities_req = Request('POST', cities_req_url,  cookies=s.cookies, headers=s.headers)
                    r = exec_request(s, cities_req, "extract_cities")
                    repl = loads(r.text)
                    for city in repl['value']:
                        res[city['title']] = city['station_id']
        except RequestError as e:
            print("Ooops! Bad Request.. Try again")
            print(e)
        except (ConnectionError, exceptions.ConnectionError) as e:
            print(e)

    # print(res)
    try:
        with conn:
            for city, code in res.items():
                conn.execute('''
                      INSERT OR REPLACE INTO City (cname, ccode) VALUES (?, ?)
                ''', (city, code))
    except sqlite3.IntegrityError:
        print(city, code)
        print("Ooops! DB integrity error..")
    conn.close()

if __name__=='__main__':
    for l, l_set in LANGS.items():
        retrieve_cities(l, l_set)