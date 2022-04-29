from cgitb import text
import requests
from bs4 import BeautifulSoup
from credentials import USERNAME, PASSWORD, HEADERS, VILLAGE_URL

from log import log

def logged_in_session():

    log("Logging in ...")

    session = requests.session()
    session.headers = HEADERS
    html = session.get(VILLAGE_URL)
    resp_parser = BeautifulSoup(html.content, 'html.parser')
    s1 = resp_parser.find('button', {'name': 's1'})['value']
    login_value = resp_parser.find('input', {'name': 'login'})['value']

    payload = {'user': USERNAME,
                'pw': PASSWORD,
                's1': s1,
                'w': '1920:1080',
                'login': login_value}
    
    session.post(VILLAGE_URL, data=payload)

    log("Login succesful")

    return session
