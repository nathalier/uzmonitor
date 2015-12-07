__author__ = 'Nathalie'

from requests import Request, Response, Session
from re import findall
from jjdecoder import JJDecoder
from json import loads

UZ_URI_BASE = "http://booking.uz.gov.ua/"
LANG = "en/"     # "uk/"
TRAINS_SEARCH = "purchase/search/"


def parse_token(body):
    s = findall("gaq.push....trackPageview...;(.+).function", body)
    command_decoded = JJDecoder(s[0]).decode()[1]
    token_decoded = findall("gv-token., \"(.+)\"", command_decoded)[0]
    return token_decoded


def needed_train(trains, needed_train):
    for train in trains:
        if train['num'] == needed_train:
            return train
    return None


def connect_to_uz(req_date, train, tr_class, passengers):
    with Session() as s:
        r = s.get(UZ_URI_BASE + LANG)
        if r.status_code == 302:
            r = s.get(UZ_URI_BASE + LANG, cookies=r.cookies)
        if r.status_code != 200:
            print("Smth went wrong. Could not connect to UZ")
            return
        gv_token = parse_token(r.text)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "charset": "UTF-8",
            "GV-Ajax": "1",
            "GV-Referer": "http://booking.uz.gov.ua/en/",
            "GV-Token": gv_token,
            ## further fields are not necessary
            # "GV-Screen": "1600x900",
            # "GV-Unique-Host": "1",
            # "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0",
            # "Referer": "http://booking.uz.gov.ua/en/"
            # "Host": "booking.uz.gov.ua",
            # "Accept-Encoding": "gzip, deflate",
            # "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            ## end of unnecessary block
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
         }

        trains_params = {"station_id_from": "2200001", "station_id_till": "2218200",
                      "station_from": "Kyiv", "station_till": "Ivano-Frankivsk",
                      "date_dep": req_date, "time_dep": "00:00", "time_dep_till": "",
                      "another_ec": "0", "search": ""}

        url = UZ_URI_BASE + LANG + TRAINS_SEARCH

        trains_req = Request('POST', url,  data=trains_params, headers=headers, cookies=s.cookies)
        prepped = trains_req.prepare()

        r = s.send(prepped)
        trains_res = loads(r.text)

        if trains_res['error']:
            print("No trains")
            return

        found_train = needed_train(trains_res['value'], train)
        if not(found_train):
            print("No places in requested train")
            print(trains_res['value'])
            return

        print(trains_res)
        print(found_train)

        # coaches_params = {"station_id_from": "2200001", "station_id_till": "2218200",
        #               "date_dep": "12.13.2015", "time_dep": "00:00", "time_dep_till": "",
        #               "another_ec": "0", "search": ""}
        #
        # url = UZ_URI_BASE + LANG + TRAINS_SEARCH
        #
        # trains_req = Request('POST', url,  data=trains_params, headers=headers, cookies=s.cookies)
        # prepped = trains_req.prepare()
        #
        # r = s.send(prepped)
        # print(r.content)


if __name__ == "__main__":
    date = "12.12.2015"
    train = "043К"
    tr_class = "К"
    passengers = []
    passengers.append("Рудь Наталія")
    passengers.append("Уткін Андрій")
    connect_to_uz(date, train, tr_class, passengers)



