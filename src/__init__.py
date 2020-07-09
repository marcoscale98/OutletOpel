#Ricorda! Stai usando la versione dei Driver per Chrome 83.0.4103.39
import json
import socket
import time
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import telegram_send
import argparse

sito = "https://vacsitmarketitopel.carusseldwt.com/result/conf/itstock"
optional_desiderati = ['Radar Pack','Rear View Camera Pack','Style Pack Black']
allestimento_desiderato = ['gs line','elegance','e-elegance']
cars_json=r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\src\\cars.json'
stderrFile = r'D:\\Marco\\Universita\\Progetti\\OpelCorsaPy\\stderr.txt'

parser = argparse.ArgumentParser()
parser.add_argument('--loop', dest='loop',action='store_true' ,help='Indicates if you want script always on')
parser.set_defaults(loop=False)
args = parser.parse_args()

def is_new_car(nuova_auto):
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
    model_select.select_by_value('6')
    time.sleep(2)

    city_input = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[5]/input")
    city_input.send_keys("10098")
    city_input.send_keys(Keys.ENTER)
    time.sleep(4)

    raggio = Select(driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[6]/label/select"))
    raggio.select_by_visible_text("100")
    time.sleep(2)

    trasm_box =driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[7]/label/select")
    trasm_box.click()
    time.sleep(2)
    trasmission = Select(trasm_box)
    trasmission.select_by_index(1) #cambio automatico
    #/html/body/div[2]/div[1]/div[2]/div[1]/div/form/div[2]/div[7]/label/select
    time.sleep(3)

def ha_optional_giusti(nuova_auto: dict, optional_che_vorrei):
    list_bool = map(lambda opt: opt in nuova_auto['optional'], optional_che_vorrei)
    for bool in list_bool:
        if not bool:
            return False
    return True


def allestimento_giusto(nuova_auto):
    for all in allestimento_desiderato:
        if all in nuova_auto['nome'].lower():
            return True
    return False


def get_new_car(cars_json='cars.json'):
    global list_auto_old, list_auto_new, link
    print("Nuova ricerca auto")
    # GET INFO
    box_auto = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div[2]")
    automobili = box_auto.find_elements_by_class_name('auto_item')
    print("Trovate", str(len(automobili)),"auto da analizzare")
    list_auto_old = {}
    list_auto_new = {}
    try:
        with open(cars_json, 'r', encoding='UTF-8') as reader:
            list_auto_old = json.load(reader)
    except FileNotFoundError:
        with open(cars_json, 'x', encoding='UTF-8') as writer:
            writer.write(json.dumps({}))
    n_auto = -1
    auto_left = True
    while auto_left or n_auto<len(automobili)-1:
        n_auto += 1
        try:
            info_box = automobili[n_auto].find_element_by_class_name('auto_content')
        except Exception as e: #non ci sono più auto
            auto_left = False
            continue
        if info_box is None:
            auto_left = False
            continue
        title_box = info_box.find_element_by_class_name('main_part').find_element_by_class_name('titles_prices').find_element_by_class_name('top_titles').find_element_by_tag_name('h2').find_element_by_tag_name('a')
        link = title_box.get_attribute('href')
        nome = title_box.text

        # controllo se aggiornare il db
        nuova_auto = {'nome': nome}
        if allestimento_giusto(nuova_auto):
            print(n_auto, '- Ho trovato questa auto con allestimento giusto', nuova_auto)
            list_auto_new[link] = nuova_auto
    #end while
    for link,car in list_auto_new.copy().items():
        driver.get(link)
        optionals = driver.find_element_by_class_name('options-optional').find_element_by_tag_name('ul').text
        #/html/body/div[2]/div[1]/div/div[1]/div[5]/div/div[2]/ul
        car['optional'] = optionals
        if ha_optional_giusti(car, optional_desiderati.copy()):
            print(n_auto, '- Ho trovato questa auto con optional corretti', car)
            if not is_new_car(car):
                list_auto_new.pop(link)
                list_auto_old.pop(link)
        else:
            list_auto_new.pop(link)

    with open(cars_json, 'w', encoding='UTF-8') as writer:
        writer.write(json.dumps(list_auto_new, indent=3))
    print("Fine ricerca")


def start_new_search(cars_json):
    global driver
    try:
        with Chrome() as driver:
            driver.get(sito)
            try:
                settings()
                get_new_car(cars_json)
            except Exception as e:
                print(e)
    except socket.gaierror:
        print("Errore di connessione")

if __name__== '__main__':
    with open(stderrFile,'w') as init:
        print(file=init)
    if args.loop:
        try:
            time.sleep(10)
            while True:
                start_new_search(cars_json)
                time.sleep(60*30)
        except Exception as e:
            with open(stderrFile, 'w') as error:
                print(e, file=error)
            raise
    else:
        start_new_search(cars_json)
