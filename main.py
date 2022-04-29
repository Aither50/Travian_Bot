import requests
import random
import time

from bs4 import BeautifulSoup
from credentials import SERVER_URL, TOWN_URL, USERNAME, PASSWORD, HEADERS, VILLAGE_URL, HERO_URL

from log_recorder import log_info

class Travian_bot:
    def __init__(self):
        self.session = requests.session()
        self.login()


    def login(self):
        
        log_info("Trying to login...")
        
        html = self.send_request(VILLAGE_URL)
        html_parser = BeautifulSoup(html, 'html.parser')

        s1 = html_parser.find('button', {'name':'s1'})['value']
        login_value = html_parser.find('input', {'name': 'login'})['value']

        payload = {
            "user": USERNAME,
            "pw": PASSWORD,
            "s1": s1,
            "w": "1920:1080",
            "login": login_value
            }

        login_attempt = self.send_request(VILLAGE_URL, data=payload)

        if login_attempt.status_code == 200:
            village_page = self.session.get(VILLAGE_URL).text
            village_page_parser = BeautifulSoup(village_page, 'html.parser')

            finder = village_page_parser.find('span', class_='ajaxReplaceableGoldAmount')
            
            if finder != -1:
                self.login_status = True 
                log_info("Login succes !")
            else:
                self.login_status = False
                log_info('Login error! Check your login data!')
        else:
            log_info('Login error! Connection error!')
        
        
    def gold_balance(self):
        """Return an int with amount of current gold"""
        village_page = self.send_request(VILLAGE_URL)
        village_page_parser = BeautifulSoup(village_page, 'html.parser')
        gold = self.clean_numbers(village_page_parser.find('span', class_='ajaxReplaceableGoldAmount').text)
        
        return gold


    def parse_resource(self, id, url):
        """Return a dict with amount of current resources"""
        village_page_parser = BeautifulSoup(url, 'html.parser')
        ressource = self.clean_numbers(village_page_parser.find('span', {'id': id }).text)
        
        return ressource


    def parse_resources_amount(self, url):
        """Takes id of resource-tag in html and return amount of this resource"""
        lumber = int(self.parse_resource('l1', url))
        clay = int(self.parse_resource('l2', url))
        iron = int(self.parse_resource('l3', url))
        crop = int(self.parse_resource('l4', url))
        free_crop = int(self.parse_resource('stockBarFreeCrop', url))
        ressource_amount = {'lumber': lumber,
                            'clay': clay,
                            'iron': iron,
                            'crop': crop,
                            'free_crop': free_crop
                            }
        
        return ressource_amount


    def check_adventure(self):
         """If any of adventures available then go"""
         hero_page = self.send_request(SERVER_URL + 'hero.php')
         hero_page_parser = BeautifulSoup(hero_page, 'html.parser')
         hero_life = hero_page_parser.find('tr', class_='attribute health tooltip' )
         
         hero_life_value = self.clean_numbers(hero_life.find('span', class_='value').text.split("%")[0])
         
         if hero_life_value < 30:
             log_info(f"Hero life is too low : {hero_life_value}. Can't be sent on adventure.")
             return False
                          
         if self.is_adventure_available():
            log_info(f"Hero life is {hero_life_value}. Going on adventure ...")
            self.go_to_adventure()

    
    def go_to_adventure(self):
        hero_page = self.send_request(HERO_URL)
        hero_page_parser = BeautifulSoup(hero_page, 'html.parser')
        link_to_adventure = hero_page_parser.find('a', {'class': 'gotoAdventure'})['href']

        confirmation_page = self.send_request(SERVER_URL + link_to_adventure)
        confirmation_page_parser = BeautifulSoup(confirmation_page, 'html.parser')
        confirmation_form_inputs = confirmation_page_parser.find_all('input')

        if confirmation_form_inputs:
            payload = {'send': confirmation_page_parser.find('input', {'name': 'send'})['value'],
                       'kid': confirmation_page_parser.find('input', {'name': 'kid'})['value'],
                       'from': confirmation_page_parser.find('input', {'name': 'from'})['value'],
                       'a': confirmation_page_parser.find('input', {'name': 'a'})['value'],
                       'start': confirmation_page_parser.find('button', {'name': 'start'})['value']}
            self.send_request(SERVER_URL + 'start_adventure.php', data=payload)
            
            log_info('Hero sent on adventure !')
        else:
            log_info('An error happened, hero was not sent on adventure')
   

    def is_adventure_available(self):
        village_page = self.send_request(VILLAGE_URL)
        village_page_parser = BeautifulSoup(village_page, 'html.parser')
        adventure_button = village_page_parser.find('button', {'class': 'adventureWhite'})
        
        try:
            adventure_count_tag = int(adventure_button.find('div', {'class': 'speechBubbleContent'}).text)
        except:
            log_info("No adventure available.")
            return False

        hero_is_available = self.is_hero_available()

        if adventure_count_tag and hero_is_available:
            return True
        
        return False


    def is_hero_available(self):
        village_page = self.send_request(VILLAGE_URL)
        village_page_parser = BeautifulSoup(village_page, 'html.parser')
        hero_is_not_available = village_page_parser.find('img', {'alt': 'on the way'})
        hero_is_available = not bool(hero_is_not_available)
        
        return hero_is_available


    def send_request(self, url, data = {}):
        try:
            if len(data) == 0:
                log_info(f"GET request on {url}")
                html = self.session.get(url, headers=HEADERS).text
                sleep_random()
                return html
            else:
                log_info(f"POST request on {url}")
                html = self.session.post(url, headers=HEADERS, data=data)
                sleep_random()
                return html
        except:
            log_info(f"Request could not be sent on {url}. Please check url.")


    def get_cost(self, id):
        url = SERVER_URL + f'build.php?id={id}'
        building_page = self.send_request(url)
        building_page_parser = BeautifulSoup(building_page, 'html.parser')
        lumber_cost = self.clean_numbers(building_page_parser.find_all('div', class_= 'inlineIcon resource')[0].text)
        clay_cost= self.clean_numbers(building_page_parser.find_all('div', class_= 'inlineIcon resource')[1].text)
        iron_cost= self.clean_numbers(building_page_parser.find_all('div', class_= 'inlineIcon resource')[2].text)
        crop_cost= self.clean_numbers(building_page_parser.find_all('div', class_= 'inlineIcon resource')[3].text)
        free_crop_cost = self.clean_numbers(building_page_parser.find_all('div', class_= 'inlineIcon resource')[4].text)
        cost = {'lumber': lumber_cost,
                'clay': clay_cost,
                'iron': iron_cost,
                'crop': crop_cost,
                'free_crop' : free_crop_cost
                            }
        
        return cost


    def clean_numbers(self, nb) -> int:
        nb_text = nb
        if nb_text.find(',') or nb_text('.') != -1:
            clean_nb = nb_text.replace(',','').replace('.','')
        else:
            clean_nb = nb_text
        return int(clean_nb)

    
    def upgrade_building(self, id):
        url = SERVER_URL + f'build.php?id={id}'
        building_page = self.send_request(url)
        building_page_parser = BeautifulSoup(building_page, 'html.parser')

        x = building_page_parser.find_all('div', class_='section1')[1].find('button',class_="green build")['onclick']
        a=x[x.find('a=')+2:x.find('&c')]
        c=x[x.find('c=')+2:x.find(';')-1]

        building_name = building_page_parser.find('div', {'id': 'content'}).find('h1', class_='titleInHeader').text.split(' level')[0]
        current_level = int(building_page_parser.find('div', {'id': 'content'}).find('h1', class_='titleInHeader').text.split(' level')[1])
        current_village = building_page_parser.find('div', {'id': 'villageNameField'}).text

        required_resources = self.get_cost(id)
        available_resources = self.parse_resources_amount(building_page)

        for key in required_resources:
            if (key in available_resources) and (available_resources[key] < required_resources[key]):
                log_info(f"Not enough resources to upgrade {building_name} to level {current_level +1} on {current_village}.")
                return False

            else:
                try:
                    self.send_request(TOWN_URL + f"?a={a}&c={c}")
                    log_info(f"Upgrading {building_name} - id: {id} - on {current_village} to level {current_level +1}")
                    log_info(f"Ressources spent : {self.get_cost(id)}")
                    return True
                except:
                    log_info(f"{building_name} - id: {id} - not upgraded. check parameters.")
                    return False
        return True


    def current_building_list(self):
        # TO DO should return the lenth of the queue + the waiting time
        # TO DO LATER handle the case of doubble building when Roman
        pass


def sleep_random(min_t = 1, max_t = 3):
    sleep_time = random.uniform(min_t, max_t)
    time.sleep(sleep_time)
    return sleep_time


if __name__ == '__main__':
    bot = Travian_bot()
    bot.upgrade_building(26)