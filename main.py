import json
import requests
import random
import time
import re

from bs4 import BeautifulSoup

from credentials import SERVER_URL, TOWN_URL, USERNAME, PASSWORD, HEADERS, VILLAGE_URL, HERO_URL
from log_recorder import log_info

class Travian_bot:

    def __init__(self):
        self.session = requests.session()
        self.session.headers = HEADERS
        self.job_todo_list = []
        self.villages = list()
        self.gold_amount = 0
        self.login()
        self.load_field_upgrade_jobs()
        self.load_village_activity()
        # print(self.villages)
        # print(self.job_todo_list)


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
                self.load_village_list(village_page)
                self.gold_balance(village_page)
            else:
                self.login_status = False
                log_info('Login error! Check your login data!')
        else:
            log_info('Login error! Connection error!')



# ------------ Action function ------------

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
    

    def build_ressource(self, village_id, resources_id):
        if not self.is_busy(village_id):
            try:
                field_url = SERVER_URL + f'build.php?newdid={village_id}&id={resources_id}'
                field_page = self.send_request(field_url)
                field_page_parser = BeautifulSoup(field_page, 'html.parser')
                onclick = field_page_parser.find('button', class_='green build')['onclick']
                link = re.match(".*'(.*)'.*", onclick).group(1)
                if link != 'disabled':
                    log_info(f"Res id : {resources_id} on {village_id} upgraded.")
                    self.send_request(SERVER_URL + link)
                    return True
                else:
                    log_info(f"Field id: {resources_id} could not be upgraded. check parameters.")
                    return False
            except:
                return "Unavailable"


    def upgrade_building(self, village_id, building_id):
        slot_id = self.get_slot_id_by_building_id(village_id, building_id)
        if slot_id == True:
            building_url = SERVER_URL + f'build.php?newdid={village_id}&id={slot_id}'
            building_page = self.send_request(building_url)
            building_page_parser = BeautifulSoup(building_page, 'html.parser')

            building_name = building_page_parser.find('div', {'id': 'content'}).find('h1', class_='titleInHeader').text.split(' level')[0]
            current_level = int(building_page_parser.find('div', {'id': 'content'}).find('h1', class_='titleInHeader').text.split(' level')[1])
            village_name = building_page_parser.find('div', {'id': 'villageNameField'}).text

            onclick = building_page_parser.find('button', class_='green build')['onclick']
            link = re.match(".*'(.*)'.*", onclick).group(1)

            if self.enough_resource_to_build(building_page) == False:
                return False
            
            if link != 'disabled':
                log_info(f"Upgrading {building_name} on {village_name}, slot id = {slot_id} to level {current_level +1}")
                self.send_request(SERVER_URL + link)
            else:
                log_info(f"{building_name} - id: {building_id} on {village_name} - not upgraded. check parameters.")
                raise Exception('Level 1')
        else:
            print("Case when building does not exists to handle")
            return False


    def build_new(self, village_id, building_to_create=0, slot_id=0):

        # TO DO : The category should be given in the source file to avoid spamming get requests 

        url = self.send_request(TOWN_URL)
        test = self.scan_building(url)
        slot = [int(item[1].replace("a","")) if int(item[2].replace("g",""))!=0 else '' for item in test]
        if slot_id in slot:
            log_info(f'There is already an existing building on the slot {slot_id}')
            return False

        for i in range(1,4):
            print(f'Reading category {i} ...')
            build_url = SERVER_URL + f'build.php?newdid={village_id}&id={slot_id}&category={str(i)}'
            build_page = self.send_request(build_url)
            build_page_parser = BeautifulSoup(build_page, 'html.parser')
            sleep_random(1,2)

            if build_page_parser.find('div', {'class': 'buildingWrapper'}) != None:
                all_possible_buildings = build_page_parser.find_all('div', class_= 'buildingWrapper')
                for building_div in all_possible_buildings:
                    building_name = building_div.find('h2').text

                    if building_name == building_to_create:
                        link = building_div.find('button', {'class': 'green new'})['onclick'].replace("window.location.href = '","").replace("'; return false;","")
        
        if self.enough_resource_to_build(build_page) == False:
                return False

        if link != None:
            log_info(f"Creating {building_to_create} on {village_id}, slot id = {slot_id}.")
            self.send_request(SERVER_URL + link)
        



# ------------ Parse function ------------

    def gold_balance(self, parser):
        """Return an int with amount of current gold"""
        village_page_parser = BeautifulSoup(parser, 'html.parser')
        gold = self.clean_numbers(village_page_parser.find('span', class_='ajaxReplaceableGoldAmount').text)
        self.gold_amount = gold
        log_info(f"You have {gold} gold")
        
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


    def scan_fields(self, parser):
        
        result = []

        field_page_parser = BeautifulSoup(parser, 'html.parser')

        fields = field_page_parser.find_all('div', {'class': 'labelLayer'})
        fields_list = [field.find_parent('div')['class'] for field in fields]
        result.extend(fields_list)

        return result      


    def scan_building(self, parser):
        
        result = []

        town_page_parser = BeautifulSoup(parser, 'html.parser')

        buildings = town_page_parser.find_all('g', {'class': 'clickShape'})
        buildings_list = [building.find_parent('div')['class'] for building in buildings]
        result.extend(buildings_list)
        
        return result 


    def get_cost(self, url):
        building_page_parser = BeautifulSoup(url, 'html.parser')
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


    def is_hero_available(self):
        village_page = self.send_request(VILLAGE_URL)
        village_page_parser = BeautifulSoup(village_page, 'html.parser')
        hero_is_not_available = village_page_parser.find('img', {'alt': 'on the way'})
        hero_is_available = not bool(hero_is_not_available)
        
        return hero_is_available


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


    def actual_building_queue(self, village_id):
        town_page = self.send_request(SERVER_URL + f'dorf1.php?newdid={village_id}')
        town_page_parser = BeautifulSoup(town_page, 'html.parser')

        try:
            queue = town_page_parser.find('div', {'class':'boxes buildingList'}).find_all('li')
            builds = []
            for item in queue:
                build = {}
                div_name = item.find('div', {'class': 'name'})
                name = div_name.contents[0].strip()
                span_level = item.find('span', {'class':'lvl'})
                level = int(re.findall(r' (\d+)', span_level.text)[0])
                div_duration = item.find('div', {'class': 'buildDuration'})
                duration = re.findall(r'(\d+:\d\d:\d\d)', div_duration.text)[0]
                time = re.findall(r' (\d+:\d\d)', div_duration.text)[0]
                build['name'] = name
                build['level'] = level
                build['duration'] = duration
                build['time'] = time
                builds.append(build)
            
            return builds      
        except:
            return "Queue empty"


    def busy_until(self, village_id):
        queue = self.actual_building_queue(village_id)
        if queue != "Queue empty":
            times = [m['time'] for m in queue if 'time' in m]
            max_time = max(times)
            return max_time
        else:
            return 0


    def is_busy(self,village_id):
        if self.actual_building_queue(village_id) == "Queue empty":
            return False
        else:
            return True


    def get_slot_id_by_building_id(self, village_id, building_id):
        try:
            town_page = self.send_request(TOWN_URL + f"?newdid={village_id}")
            town_page_parser = BeautifulSoup(town_page, 'html.parser')
            slot = town_page_parser.find('img', {'class': f'building g{building_id}'}).find_parent('div')['class']
            if slot:
                a = int(slot[1].replace("a",""))
                return a
        except AttributeError:
            print(f"Building {building_id} does not exists on village {village_id}")


    def enough_resource_to_build(self, url):

       required_resources = self.get_cost(url)
       available_resources = self.parse_resources_amount(url)

       for key in required_resources:
            if key in available_resources and available_resources[key] < required_resources[key]:
                log_info(f"Not enough resources to upgrade / build.")
                return False
            else:
                return True


# ------------ Utility function ------------

    def clean_numbers(self, nb) -> int:
        nb_text = nb
        if nb_text.find(',') or nb_text('.') != -1:
            clean_nb = nb_text.replace(',','').replace('.','')
        else:
            clean_nb = nb_text
        return int(clean_nb)


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


    def load_field_upgrade_jobs(self):
        with open('fields_to_upgrade.json', 'r') as f:
            job = json.load(f)
            self.job_todo_list = job
            # log_info(f"There are {len(job)} scheduled field upgrade jobs")


    def load_village_list(self, parser):

            # Need to parse village url, to do just after login
            log_info(f"Loading the village list ...")
            field_page_parser = BeautifulSoup(parser, 'html.parser')
            li_all = field_page_parser.find('div', {'id': 'sidebarBoxVillagelist'}).find_all('li')
            for li in li_all:
                village_name = li.find('div', {'class':"name"}).text
                village_id = li.find('a')['href'].replace("?newdid=","")
                village = {'name':village_name, 'id': village_id}
                log_info(f"Village {village_name} {village_id} found !")
                self.villages.append(village)


    def load_village_activity(self):
        log_info(f"Checking if there are constructions in the villages ...")
        for village in self.villages:
            village_status = self.busy_until(village['id'])
            village['work_left'] = village_status


    def get_build_jobs(self, village_id):
        village_to_do_list = []
        for job in self.job_todo_list:
            if (job['village_id'] == int(village_id)):
                village_to_do_list.append(job)
        return village_to_do_list

def sleep_random(min_t = 1, max_t = 3):
    sleep_time = random.uniform(min_t, max_t)
    time.sleep(sleep_time)
    return sleep_time


# ------------ Main script ------------

def main():
    tb = Travian_bot()
    try:
        for village in tb.villages:
            if village['work_left'] == 0:
                log_info(f"There is currently no construction in {village['name']}")
                job_index = 0
                job_list = tb.get_build_jobs(int(village['id']))
                number_of_jobs = len(job_list)
                log_info(f"{number_of_jobs} Found for {village['name']}")
                job_res = 1
                while (job_index < number_of_jobs and job_res > 0):
                    curr_job = job_list[job_index]
                    job_res = tb.build_ressource(curr_job['village_id'], curr_job['field_id'])
                    job_index =job_index +1
                else:
                    log_info(f"Work already in progress on {village['name']}")
    except:
        print('Error')



if __name__ == '__main__':
    main()
    
