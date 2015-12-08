__author__ = 'Nathalie'

from requests import Request, Response, Session
from re import findall
from jjdecoder import JJDecoder
from json import loads
from time import  sleep

REQ_DELAY = 3
UZ_URI_BASE = "http://booking.uz.gov.ua/"
LANG = "en/"     # "uk/"
TRAINS_SEARCH = "purchase/search/"
COACHES_SEARCH = "purchase/coaches/"
COACH_PLACES_SEARCH = "purchase/coach/"
BOOK_PLACE = "cart/add/"


class RequestError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def selected(places, num_to_book):
    odd, even = [], []
    for pl in places:
        if pl % 2 == 0:
            odd.append(pl)
        else:
            even.append(pl)
    if num_to_book == 2:
        if len(even) == 0:
            return None
        elif len(even) == 2:
            return even
        else:
            return [even[0], odd[0]]


def places_to_book(places_str, num_to_book):
    places = map(int, places_str)
    places = sorted(places)
    if num_to_book <= 4:
        block = []
        block_num = 0
        for pl in places:
            if len(block) == 0:
                block.append(pl)
                block_num = (pl - 1) // 4
            elif (pl - 1) // 4 == block_num:
                block.append(pl)
            elif (len(block) < num_to_book):
                block = []
            else:
                m = selected(block, num_to_book)
                if not m:
                    block = []
                else:
                    return m
        if len(block) >= num_to_book:
            return selected(block, num_to_book)
    return None


def book_place(s, headers, found_train, coach, place, passan):
    print("coach " + str(coach['num']) + " place " + str(place) + " for " + passan)
    (surname, name) = passan.split()
    params = {"code_station_from": found_train['from']['station_id'],
              "code_station_to": found_train['till']['station_id'],
              "train": found_train['num'], "date": found_train['from']['date'],
              "round_trip": "0", "places[0][ord]": "0", "places[0][stud]": "",
              "places[0][child]": "", "places[0][transp]": "0", "places[0][reserve]": "0",
              "places[0][bedding]":"1",
              "places[0][coach_type_id]": coach['coach_type_id'],
              "places[0][coach_num]": coach['num'],
              "places[0][coach_class]": coach['coach_class'],
              "places[0][place_num]": str(place),
              "places[0][firstname]": name,
              "places[0][lastname]": surname}

    book_place_url = UZ_URI_BASE + LANG + BOOK_PLACE

    book_place_req = Request('POST', book_place_url,  data=params, headers=headers, cookies=s.cookies)
    prepped = book_place_req.prepare()

    r = s.send(prepped)
    book_res = loads(r.text)
    if book_res['error']:
        print("No places")
        return None
    return book_res


def book_tickets(s, headers, found_train, coaches, passengers):
    for coach in coaches:
        coach_pl_res = find_places_in_coach(s, found_train, coach)

        if len(places) >= len(passengers):
            pls = places_to_book(places, len(passengers))
            if pls:
                res = None
                for place, passan in zip(pls, passengers):
                    res = book_place(s, headers, found_train, coach, place, passan)
                    if not res: break
                if res: return True
            else:
                print("not booked")
    print(coach_pl_res)
    return False


def book_1(passan):
    pass

def notify(s):
    print(s.cookies)
    cooks = s.cookies.get_dict()
    print("avascript:void(document.cookie=\"_gv_sessid=" + cooks["_gv_sessid"] +
          "; HTTPSERVERID=" + cooks["HTTPSERVERID"] + ";\")")


def parse_token(body):
    s = findall("gaq.push....trackPageview...;(.+).function", body)
    command_decoded = JJDecoder(s[0]).decode()[1]
    token_decoded = findall("gv-token., \"(.+)\"", command_decoded)[0]
    return token_decoded


def connect_to_uz(s):
    r = s.get(UZ_URI_BASE + LANG)
    if r.status_code == 302:
        r = s.get(UZ_URI_BASE + LANG)
    if r.status_code != 200:
        return False
    gv_token = parse_token(r.text)

    s.headers = {
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
    return True


def exec_request(s, req, caller = ""):
    prepped = req.prepare()
    r = s.send(prepped)
    if r.status_code != 200:
        raise RequestError(caller + ": status:" + str(r.status_code) + ": " + r.reason)
    return r


def find_trains_for_date(s, req_date):
    trains_params = {"station_id_from": "2200001", "station_id_till": "2218200",
                          "station_from": "Kyiv", "station_till": "Ivano-Frankivsk",
                          "date_dep": req_date, "time_dep": "00:00", "time_dep_till": "",
                          "another_ec": "0", "search": ""}
    trains_req_url = UZ_URI_BASE + LANG + TRAINS_SEARCH
    trains_req = Request('POST', trains_req_url,  data=trains_params, cookies=s.cookies, headers=s.headers)
    r = exec_request(s, trains_req, "find_trains_for_date")
    return loads(r.text)


def find_req_train(trains, req_train):
    for train in trains:
        if train['num'] == req_train:
            return train
    return None


def find_req_coach_type(coaches, req_coach_type):
    for coach in coaches:
        if coach['letter'] == req_coach_type:
            return coach
    return None


def find_train_coaches(s, found_train, req_coach_class):
    coaches_params = {"station_id_from": "2200001", "station_id_till": "2218200",
                    "date_dep": found_train['from']['date'], "train": found_train['num'], "coach_type": req_coach_class,
                    "model": found_train['model'], "another_ec": "0", "round_trip":"0"}
    coaches_req_url = UZ_URI_BASE + LANG + COACHES_SEARCH

    coaches_req = Request('POST', coaches_req_url,  data=coaches_params, cookies=s.cookies, headers=s.headers)
    r = exec_request(s, coaches_req, "find_train_coaches")
    return loads(r.text)


def find_places_in_coach(s, found_train, coach):
    coach_params = {"station_id_from": found_train['from']['station_id'],
                    "station_id_till": found_train['till']['station_id'],
                    "train": found_train['num'],
                    "date_dep": found_train['from']['date'], "change_scheme":"0",
                    "coach_type_id": coach['coach_type_id'],
                    "coach_num": coach['num'],
                    "coach_class": coach['coach_class']}
    coach_places_url = UZ_URI_BASE + LANG + COACH_PLACES_SEARCH

    coach_places_req = Request('POST', coach_places_url,  data=coach_params, cookies=s.cookies, headers=s.headers)
    r = exec_request(s, coach_places_req, "find_places_in_coach")
    coach_places_res = loads(r.text)
    if coach_places_res['error']:
        return []
    return coach_places_res['value']['places'][coach['prices'].popitem()[0]]


def find_and_buy(req_date, req_train_num, req_coach_class, passengers):
    with Session() as s:
        try:
            res = connect_to_uz(s)
            if not res:
                print("Smth went wrong. Could not connect to UZ")
                return

            counter = 0
            while counter < 500:
                counter += 1
                sleep(REQ_DELAY)

                ## search for trains
                trains_res = find_trains_for_date(s, req_date)

                if trains_res['error']:
                    print(str(counter) + ": No trains")
                    continue

                found_train = find_req_train(trains_res['value'], req_train_num)
                if not(found_train):
                    print(str(counter) + ": No places in requested train")
                    # print(trains_res['value'])
                    continue

                found_coach_type = find_req_coach_type(found_train['types'], req_coach_class)
                if not found_coach_type:
                    print(str(counter) + ": No requested coach type")
                    # print(found_train['types'])
                    continue

                # print(trains_res)
                # print(trains_res['value'])
                # print(found_train['types'])

                ## search for coaches
                coaches_res = find_train_coaches(s, found_train, req_coach_class)

                if coaches_res['error'] or \
                        not (coaches_res.get('value', False) and coaches_res['value'].get('coaches', False)):
                    print(str(counter) + ": No coaches")
                    continue
                # if coaches_res.get('value', None) and coaches_res['value'].get('content', None):
                #     del coaches_res['value']['content']
                # print(coaches_res['value']['coaches'])

                coaches = coaches_res['value']['coaches']
                coaches_by_place_num = sorted(coaches, key=lambda coach: coach['places_cnt'], reverse=True)
                reserved = False
                for coach in coaches_by_place_num:
                    coach['places'] = find_places_in_coach(s, found_train, coach)
                    print(str(coach['num']) + ": " + str(coach['places_cnt']) + "\\\\ " + str(coach['coach_class']))  #В Б Д - уменьшение
                    print(str(coach['num']) + ": " + str(coach['places']))
                    # if coach['places_cnt'] < len(passengers)
                return

        #######################################################################################
        ## search for coach places
                # if coaches_by_place_num[0]['places_cnt'] > len(passengers):
                #     if not book_tickets(s, headers, found_train, coaches_by_place_num, passengers):
                #         sleep(10)
                #         continue
                #     else:
                #         notify(s)
                #         return

        except RequestError as e:
            print("Ooops! Bad Request.. Try again")
            print(e)




if __name__ == "__main__":
    date = "12.24.2015"
    train_num = "115О"
    coach_class = "К"
    passengers = list()
    passengers.append("Рудь Наталія")
    passengers.append("Уткін Андрій")
    find_and_buy(date, train_num, coach_class, passengers)



