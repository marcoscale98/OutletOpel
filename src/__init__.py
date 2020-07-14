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
import telegram_send
import argparse

sito = "https://vacsitmarketitopel.carusseldwt.com/result/conf/itstock"
optional_desiderati = [
    ['Radar Pack'],
    ['Rear View Camera Pack','Park & Go Pack','Park e Go Pack'],
    ['Style Pack Black']
]
allestimento_desiderato = ['GS Line','Elegance','e-Elegance']
cars_json=r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\src\\cars.json'
stderrFile = r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\stderr.txt'
errScreenFile = r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\screenFail.png'
cap ='10098'
radius = "100"

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
        telegram_send.send(messages=[link])
    return manda_tg

def settings():
    # SETTINGS

    #scroll the page to load all the cars
    i=0
    while i<3:
        driver.execute_script("window.scrollBy(0,250)")
        i+=1
        time.sleep(2)


    model_select = Select(driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[1]/label/select"))
    if model_select is None:
        return False
    model_select.select_by_value('6')
    print("Selezionato il modello", model_select.first_selected_option.text)
    time.sleep(3)


    city_input = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[5]/input")
    if city_input is None:
        return False
    city_input.send_keys(cap)
    city_input.send_keys(Keys.ENTER)
    print("Selezionato il cap", city_input.get_attribute("value"))
    time.sleep(3)


    raggio = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[6]/label/select")
    if raggio is None:
        return False
    raggio = Select(raggio)
    if raggio is None:
        return False
    raggio.select_by_visible_text(radius)
    print("Selezionato il raggio", raggio.first_selected_option.text)
    time.sleep(3)

    trasm_box =driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[7]/label/select")
    if trasm_box is None:
        return  False
    trasmission = Select(trasm_box)
    if trasmission is None:
        return False
    trasmission.select_by_index(1) #cambio automatico
    print("Selezionato la trasmissione", trasmission.first_selected_option.text)
    time.sleep(3)
    return True

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
    box_auto = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[2]")
    automobili = box_auto.find_elements_by_class_name('auto_item')
    print("Trovate", str(len(automobili)),"auto da analizzare")

    n_auto = -1
    auto_left = True
    # estrae auto dalla lista sul sito
    while auto_left or n_auto < len(automobili) - 1:
        n_auto += 1
        try:
            info_box = automobili[n_auto].find_element_by_class_name('auto_content')
        except Exception as e:  # non ci sono più auto
            auto_left = False
            continue
        if info_box is None:
            auto_left = False
            continue
        title_box = info_box.find_element_by_class_name('main_part').find_element_by_class_name(
            'titles_prices').find_element_by_class_name('top_titles').find_element_by_tag_name(
            'h2').find_element_by_tag_name('a')
        link = title_box.get_attribute('href')
        nome = title_box.text

        # cerca se allestimento è giusto (secondo controllo)
        nuova_auto = {'nome': nome}
        if allestimento_giusto(nuova_auto):
            print(n_auto, '- Ho trovato questa auto con allestimento giusto', nuova_auto)
            list_auto_new[link] = nuova_auto
    # end while

def controlla_tutti_optional():
    # controlla che l'auto abbia gli optionals giusti e che sia nuova
    for link, car in list_auto_new.copy().items():
        driver.get(link)
        try:
            optionals = driver.find_element_by_class_name('options-optional').find_element_by_tag_name('ul').text
            car['optional'] = optionals
        except Exception as e:  # non ci sono optional
            car['optional'] = ''

        if ha_optional_giusti(car):
            print('- Ho trovato questa auto con optional corretti', car)
            if not is_new_car(car, link): #se era già presente
                list_auto_old.pop(link)
        else:
            list_auto_new.pop(link)

def cambia_allestimento(allest):
    allest_select = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[8]/label/select")
    if allest_select is None:
        return False
    allest_select = Select(allest_select)
    if allest_select is None:
        return False
    allest_select.select_by_visible_text(allest)
    print("Selezionato allestimento", allest_select.first_selected_option.text)
    time.sleep(3)
    return True

def start_new_search(cars_json):
    global driver, list_auto_old, list_auto_new
    try:
        with Chrome() as driver:
            driver.get(sito)
            ok = settings()
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
                if ok:
                    get_new_car()
            controlla_tutti_optional()
            #persistenza delle nuove auto
            with open(cars_json, 'w', encoding='UTF-8') as writer:
                writer.write(json.dumps(list_auto_new, indent=3))
            print("Fine ricerca")
    except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        print("Errore di connessione")
    except selenium.common.exceptions.NoSuchElementException as e:
        driver.save_screenshot(errScreenFile)
        with open(stderrFile,'a') as errFile:
            print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()),e, file=errFile)
            print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), "Stamped screen of the problem at ",str(errScreenFile), file=errFile)
        raise

if __name__== '__main__':
    if args.loop is not None and args.loop:
        try:
            time.sleep(int(args.delay))
            while True:
                start_new_search(cars_json)
                time.sleep(60*30)
        except Exception as e:
            with open(stderrFile, 'a') as error:
                print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()), e, file=error)
            raise
    else:
        start_new_search(cars_json)
