import configparser

config = configparser.ConfigParser()
config.read('config.ini')

SERVER_URL = config['USER']['server_url']
USERNAME = config['USER']['email']
PASSWORD = config['USER']['password']
PROXY = {'http': config['USER']['https_proxy'],
         'https': config['USER']['https_proxy']}

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}

VILLAGE_URL = SERVER_URL + 'dorf1.php'
TOWN_URL = SERVER_URL + 'dorf2.php'
HERO_URL = SERVER_URL + 'hero.php?t=3'
