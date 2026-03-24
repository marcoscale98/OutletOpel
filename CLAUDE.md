# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OutletOpel is a Python web scraper that monitors the Opel outlet website for car listings, filters them by user-specified criteria, and sends Telegram notifications for matching cars.

## Setup and Execution

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run once:**
```bash
python src/main.py
```

**Run in continuous loop (re-checks every 60 minutes):**
```bash
python src/main.py --loop
python src/main.py --loop --delay 60  # delay in seconds before first run
```

## Configuration

Edit `config.json` before running:

| Key | Required | Description |
|-----|----------|-------------|
| `path_driver` | Yes | Absolute path to ChromeDriver executable |
| `sito` | No | Opel outlet URL (has default) |
| `cambio` | No | Transmission filter (e.g. `"Automatico A 8 Rapporti"`) |
| `cap` | No | Postal code for location search (default: `"10010"`) |
| `radius` | No | Search radius in km (default: `"200"`) |
| `allestimento_desiderato` | No | Array of desired trim level strings |
| `optional_desiderati` | No | Array of desired feature/option strings |
| `cars_json` | No | Path to persistent car database (default: `"cars.json"`) |

ChromeDriver must match the installed Chrome browser version.

## Architecture

The entire application is a single file: `src/main.py` (~376 lines). All code is in Italian.

**Execution flow:**
1. `configurations()` loads `config.json` into globals
2. `config_argparser()` parses CLI flags
3. `start_new_search()` orchestrates the main loop:
   - Launches Chrome via Selenium
   - `settings(driver)` automates filter setup on the website (model, location, radius, transmission)
   - `get_new_car(driver)` scrapes paginated listing pages
   - `arricchisci_scheda_auto(driver)` visits each car's detail page to extract price and options
   - `ha_optional_giusti()` and `allestimento_giusto()` filter cars against config
   - `is_new_car()` compares against `cars.json` to detect new/updated listings
   - `send_telegram()` sends notifications for matching new cars

**Persistent state:** `cars.json` stores previously-seen cars as a dict keyed by URL, with `nome`, `optional`, and `prezzo` fields.

**Error handling:** Exceptions are appended to `stderr.txt` with timestamps; failed pages trigger a screenshot saved to `screenFail.png`.

## Known Constraints

- Uses Selenium 3 API (deprecated `find_element_by_xpath()` etc.) — incompatible with Selenium 4+
- Tightly coupled to a specific Chrome/ChromeDriver version pair
- No test suite
