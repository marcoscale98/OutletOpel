# Ricorda! Stai usando la versione dei Driver per Chrome 83.0.4103.39
import json
import pprint
import socket
import time
from typing import Dict

from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import telegram_send
import argparse
from urllib3.exceptions import NewConnectionError, MaxRetryError

DEBUG = True
STD_ERR_FILE = 'stderr.txt'
ERR_SCREEN_FILE = 'screenFail.png'
CHROMEDRIVER_LOG_PATH ='chromedriver.log'


def configurations():
    global path_driver, sito, optional_desiderati, allestimento_desiderato, cars_json, cap, radius, send_tg_message, cambio
    with open("config.json", "r") as config_file:
        config: Dict = json.load(config_file)
        path_driver = config.get("path_driver")
        if path_driver is None:
            raise Exception(
                "Manca il campo path_driver in config.json che indica il percorso dei chrome driver della versione corrente di Google Chrome")
        sito = config.get("sito", "https://vacsitmarketitopel.carusseldwt.com/result/conf/itstock")
        optional_desiderati = config.get('optional_desiderati')
        allestimento_desiderato = config.get("allestimento_desiderato")
        cars_json = config.get("database", "cars.json")
        cap = config.get("cap", "10010")
        radius = config.get("radius", "200")
        cambio = config.get("cambio")

def config_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--loop', action='store_true', help='Indicates if you want script always on')
    parser.add_argument('--delay', dest='delay', help='Indicates seconds of delay before running the loop')
    parser.add_argument('--send-tg-alerts', action='store_false', help='Indicates if you want to send telegram alerts', dest='send_tg_alerts')
    parser.set_defaults(delay=1)
    return parser.parse_args()


def is_rendering(driver):
    try:
        rend = driver.find_element_by_xpath(
            "/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[8]/label/span/img")
        style = rend.get_attribute("style")
        if style == "display:none":
            return False
        print("Sto caricando")
        return True
    except Exception as e:
        return False


def is_new_car(nuova_auto, link):
    """True se la nuova auto non era presente, oppure era presente ma si è aggiornata"""
    res = False
    if link in list_auto_old:
        if list_auto_old[link] != nuova_auto:
            res = True
    else:
        res = True
    return res



def settings(driver):
    # SETTINGS
    # try:
    #     driver.find_element_by_xpath("/html/body").find_element_by_id("main-frame-error")
    #     print("Errore di connessione")
    #     return False
    # except selenium.common.exceptions.NoSuchElementException:
    #     pass

    #id: _psaihm_id_accept_all_btn
    #accept cookie
    try:
        accept_cookie_btn = driver.find_element_by_id('_psaihm_id_accept_all_btn')
        accept_cookie_btn.click()
    except NoSuchElementException as e:
        pass

    # select opel corsa model
    try:
        #model_select = Select(
            # driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[1]/label/select"))
        model_select = driver.find_element_by_name('modelContainer:modelGroup')
        model_select = Select(model_select)
    except NoSuchElementException:
        print("Non ho trovato il modello 'Corsa'")
        return False
    model_select.select_by_value('6')
    # check if i selected 'corsa' model
    selezionato = model_select.first_selected_option.text
    if selezionato == "Corsa":
        print("Selezionato il modello", selezionato)
    else:
        return False
    time.sleep(3)

    # select the city where find the car
    #city_input = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[5]/input")
    city_input = driver.find_element_by_name('zipCodeContainer:zipCode')
    if city_input is None:
        print('Non ho trovato il cap da selezionare nella pagina')
        return False
    city_input.send_keys(cap)
    city_input.send_keys(Keys.ENTER)
    # check if i selected the right cap
    selezionato = city_input.get_attribute("value")
    if selezionato == cap:
        print("Selezionato il cap", selezionato)
    else:
        print('Non ho selezionato il giusto cap nella pagina')
        return False
    time.sleep(3)

    # select the radius of the search
    # raggio = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[6]/label/select")
    raggio = driver.find_element_by_name('radiusContainer:radius')
    if raggio is None:
        print("Raggio non trovato nella pagina")
        return False
    raggio = Select(raggio)
    if raggio is None:
        return False
    raggio.select_by_visible_text(radius)
    # check if i selected the right radius
    selezionato = raggio.first_selected_option.text
    if selezionato == radius:
        print("Selezionato il raggio", selezionato)
    else:
        return False
    time.sleep(3)

    # select the automatic gear selector
    if cambio:
        try:
            trasm_box = driver.find_element_by_name('gearTypeContainer:gearType')
            if trasm_box is None:
                print("Non ho trovato il box per selezionare il cambio")
            trasmission = Select(trasm_box)
            trasmission.select_by_visible_text(cambio)
            selezionato = trasmission.first_selected_option.text
            if selezionato == cambio:
                print("Selezionato la trasmissione", selezionato)
            else:
                print("Non ho selezionato il giusto cambio")
                return False
            time.sleep(3)
        except NoSuchElementException:
            print("Non ho trovato il box per selezionare il cambio")
            return False
    return True


def scroll_page(driver):
    # scroll the page to load all the cars
    i = 0
    while i < 10:
        driver.execute_script("window.scrollBy(0,250)")
        i += 1
        time.sleep(1)


def ha_optional_giusti(nuova_auto: dict):
    i = 0
    trovato_corretto = True
    while trovato_corretto and optional_desiderati is not None and i < len(optional_desiderati):
        j = 0
        is_present = False
        while (not is_present) and j < len(optional_desiderati[i]):
            is_present = optional_desiderati[i][j].lower() in nuova_auto['optional'].lower()
            j += 1
        trovato_corretto = is_present
        i += 1

    return trovato_corretto


def allestimento_giusto(nuova_auto):
    for all in allestimento_desiderato:
        if all.lower() in nuova_auto['nome'].lower():
            return True
    return False


def get_new_car(driver):
    """
    Analizza tutte le auto presenti sul sito
    Prerequisiti: aver settato le impostazioni
    """
    print("Analizzo nuovo blocco auto")
    # GET INFO
    auto_left = True
    page_left = True
    n_page = 0
    # estrae auto dalla lista sul sito
    while page_left:
        scroll_page(driver)
        box_auto = driver.find_element_by_class_name("page_right")
        automobili = box_auto.find_elements_by_class_name('auto_item')
        print("Trovate", str(len(automobili)), "auto da analizzare nella pagina numero", n_page + 1)
        n_page += 1
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
            nuova_auto = {'nome': nome}
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
            print("Ho cambiato pagina")
        except NoSuchElementException:
            page_left = False


def send_telegram(link, nuova_auto):
    messaggio = "<a href='{0}'>{1} al prezzo di: {2}</a>".format(link, nuova_auto['nome'], nuova_auto['prezzo'])
    telegram_send.send(messages=[messaggio], parse_mode="html")


def arricchisci_scheda_auto(driver):
    """
    controlla che l'auto abbia gli optionals giusti e che sia nuova
    :param driver:
    :return:
    """
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
        except NoSuchElementException:  # non c'è scritto il prezzo
            car['prezzo'] = ""

        if ha_optional_giusti(car):
            print('- Ho trovato questa auto con optional corretti')
            pprint.pprint(car, indent=2)
            is_new_car_ = is_new_car(car, link)
            if not is_new_car_:  # se era già presente
                list_auto_old.pop(link)
            else:
                if args.send_tg_alerts:
                    send_telegram(link, car)
        else:
            list_auto_new.pop(link)


def cambia_allestimento(allest, driver):
    try:
        # allest_select = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[8]/label/select")
        allest_select = driver.find_element_by_name("serieTypeContainer:serieType")
        if allest_select is None:
            print("Box per inserire allestimento non trovato")
        allest_select = Select(allest_select)
        allest_select.select_by_visible_text(allest)
        selezionato = allest_select.first_selected_option.text
        if selezionato == allest:
            print("Selezionato allestimento", selezionato)
            time.sleep(3)
        else:
            print("Non ho selezionato il giusto allestimento")
            return False
        return True
    except NoSuchElementException:
        print("Box per inserire allestimento non trovato")
        return False


def start_new_search(cars_json, path_driver):
    global list_auto_old, list_auto_new
    try:
        with Chrome(executable_path=path_driver, service_log_path=CHROMEDRIVER_LOG_PATH) as driver:
            driver: Chrome = driver
            driver.get(sito)
            ok = settings(driver)
            if not ok:
                return
            list_auto_old = {}
            list_auto_new = {}
            # carica le auto già visualizzate in passato
            try:
                with open(cars_json, 'r', encoding='UTF-8') as reader:
                    list_auto_old = json.load(reader)
            except FileNotFoundError:
                with open(cars_json, 'x', encoding='UTF-8') as writer:
                    writer.write(json.dumps({}))
            print("Nuova ricerca auto")
            if allestimento_desiderato:
                for al in allestimento_desiderato:
                    if ok:
                        ok = cambia_allestimento(al, driver)
                    else:
                        return
                    if ok:
                        get_new_car(driver)
                    else:
                        return
            else:
                get_new_car(driver)
            arricchisci_scheda_auto(driver)
            # persistenza delle nuove auto
            with open(cars_json, 'w', encoding='UTF-8') as writer:
                writer.write(json.dumps(list_auto_new, indent=3))
            print("Fine ricerca")
    except (ConnectionRefusedError, socket.gaierror, NewConnectionError, MaxRetryError,ConnectionError):
        print("Errore di connessione")
    except NoSuchElementException as e:
        with open(STD_ERR_FILE, 'a') as errFile:
            print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), e, file=errFile)
        if DEBUG:
            raise


if __name__ == '__main__':
    global args
    configurations()
    args = config_argparser()
    if args.loop is not None and args.loop:
        try:
            time.sleep(int(args.delay))
            while True:
                start_new_search(cars_json, path_driver)
                time.sleep(60 * 60)
        except Exception as e:
            with open(STD_ERR_FILE, 'a') as error:
                print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), e, file=error)
            if DEBUG:
                raise
    else:
        start_new_search(cars_json, path_driver)
