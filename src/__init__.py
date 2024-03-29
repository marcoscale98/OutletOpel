#Ricorda! Stai usando la versione dei Driver per Chrome 83.0.4103.39
import json
import socket
import time

import requests
import selenium.common.exceptions
import urllib3
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import telegram_send
import argparse

DEBUG = True
with open("config.json","r") as config:
    config = json.load(config)
    if config["path_driver"] is not None:
        path_driver=config["path_driver"]
    else:
        raise Exception("Manca il campo path_driver in config.json che indica il percorso dei chrome driver della versione corrente di Google Chrome")
    if config['sito'] is not None:
        sito = config['sito']
    else:
        sito = "https://vacsitmarketitopel.carusseldwt.com/result/conf/itstock"
    optional_desiderati = []
    if config['optional_desiderati'] is not None:
        optional_desiderati = config['optional_desiderati']
    allestimento_desiderato = []
    if config["allestimento_desiderato"] is not None:
        allestimento_desiderato = config["allestimento_desiderato"]
    cars_json = "cars.json"
    if  config["database"] is not None:
        cars_json = config["database"]
    stderrFile = r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\stderr.txt'
    errScreenFile = r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\screenFail.png'
    cap = "10010"
    if config["cap"] is not None:
        cap = config["cap"]
    radius = "200"
    if config["radius"] is not None:
        radius = config["radius"]

parser = argparse.ArgumentParser()
parser.add_argument('--loop',action='store_true' ,help='Indicates if you want script always on')
parser.add_argument('--delay',dest='delay',help='indicates seconds of delay before running the loop')
parser.set_defaults(delay=1)
args = parser.parse_args()

def is_rendering():
    try:
        rend = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[8]/label/span/img")
        style = rend.get_attribute("style")
        if style == "display:none":
            return False
        print("Sto caricando")
        return True
    except Exception as e:
        return False

#true se la nuova auto non era presente, oppure era presente ma si è aggiornata
def is_new_car(nuova_auto, link):
    manda_tg = False
    if link in list_auto_old:
        if list_auto_old[link] != nuova_auto:
            manda_tg = True
    else:
        manda_tg = True
    if manda_tg:
        messaggio = "<a href='{0}'>{1} al prezzo di: {2}</a>".format(link, nuova_auto['nome'],nuova_auto['prezzo'])
        telegram_send.send(messages=[messaggio], parse_mode="html")
    return manda_tg

def settings():
    # SETTINGS
    try:
        driver.find_element_by_xpath("/html/body").find_element_by_id("main-frame-error")
        print("Errore di connessione")
        return False
    except selenium.common.exceptions.NoSuchElementException:
        pass
    try:
        model_select = Select(driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[1]/label/select"))
    except NoSuchElementException:
        print("Errore di connessione")
        return False
    model_select.select_by_value('6')
    selezionato = model_select.first_selected_option.text
    if selezionato == "Corsa":
        print("Selezionato il modello", selezionato)
    else:
        return False
    time.sleep(3)

    city_input = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[5]/input")
    if city_input is None:
        return False
    city_input.send_keys(cap)
    city_input.send_keys(Keys.ENTER)
    selezionato = city_input.get_attribute("value")
    if  selezionato == cap:
        print("Selezionato il cap", selezionato)
    else:
        return False
    time.sleep(3)


    raggio = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[6]/label/select")
    if raggio is None:
        return False
    raggio = Select(raggio)
    if raggio is None:
        return False
    raggio.select_by_visible_text(radius)
    selezionato = raggio.first_selected_option.text
    if selezionato == radius:
        print("Selezionato il raggio", selezionato)
    else:
        return False
    time.sleep(3)

    try:
        trasm_box =driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[7]/label/select")
        trasmission = Select(trasm_box)
        trasmission.select_by_index(1)  # cambio automatico
        selezionato = trasmission.first_selected_option.text
        if selezionato == "Cambio automatico":
            print("Selezionato la trasmissione", selezionato)
        else:
            return False
        time.sleep(3)
    except NoSuchElementException:
        return False
    return True


def scroll_page():
    # scroll the page to load all the cars
    i = 0
    while i < 3:
        driver.execute_script("window.scrollBy(0,250)")
        i += 1
        time.sleep(2)


def ha_optional_giusti(nuova_auto: dict):
    i=0
    trovato_corretto = True
    while (trovato_corretto) and i<len(optional_desiderati):
        j = 0
        is_present=False
        while (not is_present) and j<len(optional_desiderati[i]):
            is_present = optional_desiderati[i][j].lower() in nuova_auto['optional'].lower()
            j+=1
        trovato_corretto = is_present
        i+=1

    return trovato_corretto

def allestimento_giusto(nuova_auto):
    for all in allestimento_desiderato:
        if all.lower() in nuova_auto['nome'].lower():
            return True
    return False

def get_new_car():
    print("Analizzo nuovo blocco auto")
    # GET INFO
    auto_left = True
    page_left = True
    n_page = 0
    # estrae auto dalla lista sul sito
    while page_left:
        box_auto = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[2]")
        automobili = box_auto.find_elements_by_class_name('auto_item')
        print("Trovate", str(len(automobili)), "auto da analizzare nella pagina numero", n_page)
        n_page+=1
        n_auto = 0
        while auto_left and n_auto < len(automobili):
            try:
                info_box = automobili[n_auto].find_element_by_class_name('auto_content')
            except NoSuchElementException as e:  # non ci sono più auto
                auto_left = False
                continue
            try:
                title_box = info_box.find_element_by_class_name('main_part').find_element_by_class_name(
                'titles_prices').find_element_by_class_name('top_titles').find_element_by_tag_name(
                'h2').find_element_by_tag_name('a')
            except NoSuchElementException:
                print(n_auto, '- title_box non trovata')
                continue
            try:
                link = title_box.get_attribute('href')
            except NoSuchElementException:
                print(n_auto, "- link non trovato")
                continue
            try:
                nome = title_box.text
            except NoSuchElementException:
                print(n_auto, "- nome non trovato")
                continue
            # cerca se allestimento è giusto (secondo controllo)
            nuova_auto = {'nome': nome}
            #if allestimento_giusto(nuova_auto):
            print(n_auto, '- Ho trovato questa auto con allestimento giusto', nuova_auto)
            if link in list_auto_new:
                print(link, "- è già presente")
            list_auto_new[link] = nuova_auto
            n_auto += 1
        # end while
        # cambio pagina
        try:
            tasto_cambio_pagina = box_auto.find_element_by_class_name("index_top")
            tasto_cambio_pagina = tasto_cambio_pagina.find_element_by_class_name("small_search_results_pager")
            tasto_cambio_pagina = tasto_cambio_pagina.find_element_by_tag_name("ul")
            tasto_cambio_pagina = tasto_cambio_pagina.find_element_by_class_name("to-right")
            tasto_cambio_pagina = tasto_cambio_pagina.find_element_by_tag_name("a")
            tasto_cambio_pagina.click()
            time.sleep(3)
            #scroll_page()
            print("Ho cambiato pagina")
        except NoSuchElementException:
            page_left = False

def arricchisci_scheda_auto():
    # controlla che l'auto abbia gli optionals giusti e che sia nuova
    print("Controllo le pagine di", len(list_auto_new), "auto")
    for link, car in list_auto_new.copy().items():
        driver.get(link)
        try:
            optionals = driver.find_element_by_class_name('options-optional').find_element_by_tag_name('ul').text
            car['optional'] = optionals
        except Exception as e:  # non ci sono optional
            car['optional'] = ''
        try:
            prezzo_box = driver.find_element_by_class_name("gross_price_new")
            car['prezzo'] = prezzo_box.text
        except NoSuchElementException: #non c'è scitto il prezzo
            car['prezzo']=""

        if ha_optional_giusti(car):
            print('- Ho trovato questa auto con optional corretti', car)
            if not is_new_car(car, link): #se era già presente
                list_auto_old.pop(link)
        else:
            list_auto_new.pop(link)

def cambia_allestimento(allest):
    try:
        allest_select = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[8]/label/select")
        allest_select = Select(allest_select)
        allest_select.select_by_visible_text(allest)
        selezionato = allest_select.first_selected_option.text
        if selezionato == allest:
            print("Selezionato allestimento", selezionato)
            time.sleep(3)
        else:
            return False
        return True
    except NoSuchElementException:
        return False

def start_new_search(cars_json,path_driver):
    global driver, list_auto_old, list_auto_new
    try:
        with Chrome(executable_path=path_driver) as driver:
            driver.get(sito)
            ok = settings()
            if not ok:
                return
            list_auto_old = {}
            list_auto_new = {}
            try:
                with open(cars_json, 'r', encoding='UTF-8') as reader:
                    list_auto_old = json.load(reader)
            except FileNotFoundError:
                with open(cars_json, 'x', encoding='UTF-8') as writer:
                    writer.write(json.dumps({}))
            print("Nuova ricerca auto")
            for al in allestimento_desiderato:
                if ok:
                    ok = cambia_allestimento(al)
                else:
                    return
                if ok:
                    get_new_car()
                else:
                    return
            arricchisci_scheda_auto()
            #persistenza delle nuove auto
            with open(cars_json, 'w', encoding='UTF-8') as writer:
                writer.write(json.dumps(list_auto_new, indent=3))
            print("Fine ricerca")
    except (ConnectionRefusedError,socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        print("Errore di connessione")
    except selenium.common.exceptions.NoSuchElementException as e:
        with open(stderrFile,'a') as errFile:
            print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()),e, file=errFile)
        if DEBUG:
            raise

if __name__== '__main__':
    if args.loop is not None and args.loop:
        try:
            time.sleep(int(args.delay))
            while True:
                start_new_search(cars_json,path_driver)
                time.sleep(60*60)
        except Exception as e:
            with open(stderrFile, 'a') as error:
                print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), e, file=error)
            if DEBUG:
                raise
    else:
        start_new_search(cars_json,path_driver)
