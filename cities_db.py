__author__ = 'Nathalie'

import sqlite3
from requests import Session, Request, exceptions
from requester import connect_to_uz, exec_request, RequestError, UZ_URI_BASE
from os import path
import sys
from json import loads
from string import ascii_lowercase


DB_NAME = 'cities.sqlite'
LANGS = ['en']
STATION_SEARCH = 'purchase/station/'

if __name__=='__main__':
    if path.isfile(DB_NAME):
        upd = input('Database already exists. Update it? (Yes | Any-key): ')
        if upd.lower() != 'yes':
            sys.exit()  #raise SystemExit

    conn = sqlite3.connect(DB_NAME)
    conn.executescript('''
        DROP TABLE IF EXISTS City;
        DROP TABLE IF EXISTS Lang;

        CREATE TABLE Lang(
           lang TEXT NOT NULL UNIQUE,
           code TEXT NOT NULL UNIQUE
        );

        INSERT INTO Lang VALUES ('english', 'en');

        CREATE TABLE City(
          cname TEXT NOT NULL UNIQUE,
          ccode TEXT NOT NULL UNIQUE,
          lang TEXT
        )

        ''')
    conn.commit()

    res = {}
    with Session() as s:
        try:
            connect_to_uz(s)

            for lang in LANGS:
                res[lang] = {}
                for char_1 in ascii_lowercase:
                    for char_2 in ascii_lowercase:
                        cities_req_url = UZ_URI_BASE + lang + '/' + STATION_SEARCH + char_1 + char_2
                        cities_req = Request('POST', cities_req_url,  cookies=s.cookies, headers=s.headers)
                        r = exec_request(s, cities_req, "extract_cities")
                        repl = loads(r.text)
                        for city in repl['value']:
                            res[lang][city['title']] = city['station_id']
        except RequestError as e:
            print("Ooops! Bad Request.. Try again")
            print(e)
        except (ConnectionError, exceptions.ConnectionError) as e:
            print(e)

    for lang, cities in res.items():
        for city, code in cities.items():
            conn.execute('''
                  INSERT INTO City (cname, ccode, lang) VALUES (?, ?, ?)
            ''', (city, code, lang))
    conn.commit()
    conn.close()