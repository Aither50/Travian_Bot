from configparser import ConfigParser

config = ConfigParser()
config.sections()
config.read('config.ini')

SERVER_URL = config['USER']['server']
VILLAGE_URL = SERVER_URL + 'dorf1.php'
USERNAME = config['USER']['username']
PASSWORD = config['USER']['password']

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en,en-US;q=0.8,ru-RU;q=0.6,ru;q=0.4',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36'
}
