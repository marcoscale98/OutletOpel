# Requisiti
- python 3.9 o superiore
- Lanciare da terminale `pip install -r requirements.txt`
- Avere Google Chrome installato
- Installare i google driver corrispondenti alla versione corrente di Google Chrome([link dove scaricare i driver](https://chromedriver.chromium.org/))
- Inserire in _config.json_ il percorso ai driver in `path_driver`
## Problemi
Quando si sfoglia tra le pagine di una ricerca potrebbero capitare dei 
duplicati. è un problema del sito

## Come lanciarlo
Passi:
- Modificare il file _config.json_ con i seguenti parametri:
  - _cars_json_(opzionale): path del file dove memorizzare le auto già visualizzate
  - _path_driver_: path dell'eseguibile dei driver di Chrome
  - _sito_ (opzionale): sito opel outlet
  - _allestimento_desiderato_ (opzionale): array di stringhe con il nome degli allestimenti desiderati
- `python src/main.py`
