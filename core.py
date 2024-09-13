import tkinter as tk
from tkinter import simpledialog
import pyautogui
import time
import json
import os
import pytesseract
from PIL import ImageGrab
import random
import keyboard
import sys
import mouse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import pygetwindow as gw
import threading

# Redirect print function
class StdoutRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        self.widget.insert(tk.END, message)
        self.widget.see(tk.END)

    def flush(self):
        pass

# Global variables and configurations
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
running = False
fighting = False
fight_state = 0
role = ''
attack_counter = 0

CHARACTER_JSON_PATH = 'configs/MrHustle.json'  # Update this to get character name

CONFIG = {
    "name": "CharacterName",
    "class": "dps",
    "leader": False,
    "whistle": False,
    "inventory": [],
    "equipment": {
        "weapon": {},
        "armor": {},
        "charms": [],
        "glyphs": []
    }
}

# Load the scoring system from JSON
def load_scoring_system():
    with open('jsons/itemScore.json', 'r') as file:
        return json.load(file)
scoring_system = load_scoring_system()

# Function to update overlay position
def update_overlay_position():
    global fighting
    while fighting != True:
        try:
            # Get the Chrome window
            chrome_window = gw.getWindowsWithTitle("Ladder Slasher v1.33.1")[0]
            if chrome_window:
                # Check if Chrome is minimized
                if chrome_window.isMinimized:
                    print('Chrome Window Minimized')
                    #overlay.withdraw()  # Hide the overlay
                    overlay.attributes('-topmost', False)
                else:
                    # Position overlay on top of Chrome
                    print('Chrome Window NOT Minimized')
                    chrome_pos = chrome_window.topleft
                    newX = chrome_pos.x + 1000 
                    newY = chrome_pos.y + 730
                    overlay.geometry(f"500x400+{newX}+{newY}")
                    overlay.deiconify()  # Show the overlay if hidden
                    #overlay.attributes('-topmost', True)
            time.sleep(1)  # Check every second
        except IndexError:
            pass  # Handle case where window might not be found
    if fighting == True:
        print('fighting = true')
        try:
            # Get the Chrome window
            chrome_window = gw.getWindowsWithTitle("Ladder Slasher v1.33.1")[0]
            if chrome_window:
                # Check if Chrome is minimized
                if chrome_window.isMinimized:
                    print('Chrome Window Minimized')
                    #overlay.withdraw()  # Hide the overlay
                    overlay.attributes('-topmost', False)
                else:
                    # Position overlay on top of Chrome
                    print('Chrome Window NOT Minimized')
                    chrome_pos = chrome_window.topleft
                    newX = chrome_pos.x + 1000
                    newY = chrome_pos.y + 730
                    overlay.geometry(f"500x400+{newX}+{newY}")
                    overlay.deiconify()  # Show the overlay if hidden
                    #overlay.attributes('-topmost', True)
            time.sleep(1)  # Check every second
        except IndexError:
            pass  # Handle case where window might not be found
            
# Selenium setup
def setup_browser():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
    driver = webdriver.Chrome(options=chrome_options, service=Service(r"C:\Windows\System32\chromedriver.exe"))
    return driver

def write_to_terminal(message):
    terminal_output.insert(tk.END, message + '\n')
    terminal_output.see(tk.END)

def getCharacter(driver):
    global CHARACTER_JSON_PATH, CONFIG
    characterName = driver.find_element(By.CSS_SELECTOR, ".cName").text
    print(f'characterName: {characterName}')
    charJsonPath = 'configs/' + characterName
    charJsonPath = charJsonPath + '.json'
    print(f'charJsonPath: {charJsonPath}')
    CHARACTER_JSON_PATH = charJsonPath
    CONFIG = loadConfig()
    return

# Load character data from JSON
def loadConfig():
    if os.path.exists(CHARACTER_JSON_PATH):
        with open(CHARACTER_JSON_PATH, 'r') as file:
            return json.load(file)
    else:
        return CONFIG

def saveConfig():
    with open(CHARACTER_JSON_PATH, 'w') as file:
        json.dump(CONFIG, file, indent=4)

def update_character_json(driver):
    global CONFIG
    CONFIG["inventory"] = scan_inventory(driver)
    CONFIG["equipment"] = scan_equipment(driver)
    
    saveConfig()

def move_to_position(driver, move_class):
    try:
        button = driver.find_element(By.CLASS_NAME, move_class)
        button.click()
        time.sleep(1)  # Allow some time for movement to process
    except Exception as e:
        write_to_terminal(f"Error moving to position: {e}")

def ensure_position(driver, expected_position):
    try:
        position_element = driver.find_element(By.CLASS_NAME, 'charImg')
        current_position = position_element.get_attribute('class')
        if expected_position not in current_position:
            if 'posBack' in expected_position:
                move_to_position(driver, 'moveL')
            elif 'posFront' in expected_position:
                move_to_position(driver, 'moveR')
    except Exception as e:
        write_to_terminal(f"Error ensuring position: {e}")


def scan_inventory(driver):
    inventory_items = driver.find_elements(By.CSS_SELECTOR, ".invEqBox .itemBox")
    inventory = []
    
    for item in inventory_items:
        hover_and_print_item_details(driver, item)
        time.sleep(0.5)  # Allow time for the hover popup to appear
        item_details = driver.find_element(By.CSS_SELECTOR, ".tipBox.tbItemDesc").get_attribute('outerHTML')
        parsed_item = parse_gear_details(item_details)
        print(f"parsed_item: {parsed_item}")
        inventory.append(parsed_item)
        #inventory.append(parse_item_details(item_details))
    
    return inventory

def scan_equipment(driver):
    equipped_items = driver.find_elements(By.CSS_SELECTOR, ".invEquipped .itemBox")
    equipment = {
        "weapon": {},
        "armor": {},
        "charms": [],
        "glyphs": []
    }
    
    for item in equipped_items:
        slot = item.get_attribute("data-slot")
        hover_and_print_item_details(driver, item)
        time.sleep(0.3)  # Allow time for the hover popup to appear
        item_details = driver.find_element(By.CSS_SELECTOR, ".tipBox.tbItemDesc").get_attribute('outerHTML')
        print(f'********')
        print(f'Item Details: {item_details}')
        #parsed_item = parse_item_details(item_details)
        parsed_item = parse_gear_details(item_details)
        print(f"parsed_item: {parsed_item}")
        if slot == "weapon":
            equipment["weapon"] = parsed_item
        elif slot == "armor":
            equipment["armor"] = parsed_item
      #  elif "charm" in slot:
      #      equipment["charms"].append(parsed_item)
      #  elif "glyph" in slot:
      #      equipment["glyphs"].append(parsed_item)
    
    return equipment

def parse_item_details(item_html):
    # Implement your logic to parse item details from the HTML
    # Return a dictionary with item details
    return {"html": item_html}  # Placeholder, replace with actual parsing logic

def parse_gear_details(html):
    soup = BeautifulSoup(html, 'html.parser')
    item_details = {}

    # Try to locate the first `itemdescBox`
    item_box = soup.find('div', class_='itemDescBox')

    if not item_box:
        print("Item_box not found")
        return None

    # Continue parsing if found
    item_name = item_box.find('div', class_='fcb fwb').text.strip()
    item_details['name'] = item_name
    print(f'item_details -- {item_details}')

    # Find all stats inside this specific itemdescBox
    stats = item_box.find_all('div', class_='fcb')

    for stat in stats:
        text = stat.text.strip()
        if 'Level Req' in text:
            item_details['level_req'] = text.split(': ')[1]
        elif 'Damage' in text:
            item_details['damage'] = text.split(': ')[1]
        elif 'Defense' in text:
            defense_type = 'physical_defense' if 'Physical' in text else 'magical_defense'
            item_details[defense_type] = text.split(': ')[1]
        elif 'Mana Cost' in text:
            item_details['mana_cost'] = text.split(': ')[1]
        elif 'Heals' in text:
            item_details['heals'] = text.split(': ')[1]
        elif '%' in text:
            item_details[text.split('% ')[1]] = text.split('% ')[0]
        elif ' to ' in text:
            wrongName = text.split(' to ')[1]
            newName = wrongName.split(' ')[1]
            leftStat = text.split(' to ')[0]
            rightStat = wrongName.split(' ')[0]
            newStat = leftStat + ' to ' + rightStat
            item_details[newName] = newStat
        else:
            # General attribute handling
            parts = text.split(' ')
            if len(parts) > 1:
                stat_name = ' '.join(parts[:-1])
                stat_value = parts[-1]
                item_details[stat_name.lower().replace(' ', '_')] = stat_value

    return item_details
   
def hover_and_print_item_details(driver, item_element):
    try:
        time.sleep(.5)
        # Move to the item to trigger the hover effect
        actions = ActionChains(driver)
        actions.move_to_element(item_element).perform()

        # Pause for a moment to allow the popup to appear
        time.sleep(0.5)

        # Locate the popup div that appears when hovering
        popup = driver.find_element(By.CSS_SELECTOR, ".tipBox.tbItemDesc")

        # Print the popup's HTML content
        print(popup.get_attribute('outerHTML'))

    except Exception as e:
        write_to_terminal(f"Error while hovering and printing item details: {e}")


# LOOT SYSTEM

def hover_and_extract_item(driver, item_element):
    try:
        # Hover over the item
        actions = ActionChains(driver)
        actions.move_to_element(item_element).perform()
        time.sleep(0.5)  # Wait for hover effect to trigger

        # Capture item details from popup
        popup = driver.find_element(By.CSS_SELECTOR, ".tipBox.tbItemDesc")
        item_html = popup.get_attribute('outerHTML')
        parsed_item = parse_gear_details(item_html)

        return parsed_item

    except Exception as e:
        print(f"Error hovering over item: {e}")
        return None

def log_item_to_file(item_details, item_score, filename="logs/itemDrops.txt"):
    with open(filename, 'a') as log_file:
        log_file.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        log_file.write(f"Item Name: {item_details['name']}\n")
        log_file.write(f"Item Details: {item_details}\n")
        log_file.write(f"Item Score: {item_score}\n")
        log_file.write("----- Stats -----\n")
        # Log other item details (such as stats)
        for stat, value in item_details.items():
            if stat != 'name':
                log_file.write(f"{stat.replace('_', ' ').capitalize()}: {value}\n")

        log_file.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n")


def parse_and_score_drops_new(driver, drop_items):
    loot_threshold = 10
    print('--- Score Drops ---')

    # Log file name
    log_filename = "logs/itemDrops.txt"
    
    for item in drop_items:
        parsed_item = hover_and_extract_item(driver, item)
        if parsed_item:
            print(f'parsed_item = {parsed_item}')
            item_score = calculate_item_score(parsed_item['name'], parsed_item)
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f"Item: {parsed_item['name']}, Score: {item_score}")
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
            # Log the item to file
            log_item_to_file(parsed_item, item_score, log_filename)


            print(f'Check if item_score > loot_threshold -------------- {item_score} > {loot_threshold}')
            # Decide if the item should be looted
            if item_score > loot_threshold:
                print('TRY TO LOOT ITEM')
                loot_item(driver, item)


# Function to calculate the score of an item based on its name and modifiers
def calculate_item_score(item_name, modifiers):
    #print(f'-Scoring Modifiers- {modifiers}')
    score = 0
    if item_name in scoring_system:
        score += scoring_system[item_name]["base_score"]
        for mod in modifiers:
            print(f"Mod: {mod}")
            if mod in scoring_system[item_name]["modifiers"]:
                score += scoring_system[item_name]["modifiers"][mod]
    print('| *** Calculate Item Score ***')
    print(f'| Item Name: {item_name}')
    for mod in modifiers:
        print(f'{mod}')
    if "Enhanced Effect" in modifiers:
        score += 100  # Example of boosting score based on a stat
    if "Experience" in modifiers:
        score += 50  # Example of boosting score based on a stat
    if "Vitality" in modifiers:
        score += 50
    if "Max Life" in modifiers:
        score += 50
    if "Life Regen" in modifiers:
        score += 10
    if "Life Steal" in modifiers:
        score += 50
    if "Parry" in modifiers:
        score += 50
    if "Crit" in modifiers:
        score += 50
    if "Intelligence" in modifiers:
        score += 50
    if "Life per Attack" in modifiers:
        score += 50
    if "Reduction" in modifiers:
        score += 50
    if "Pierce" in modifiers:
        score += 50

    print(f'Score = {score}')
    return score







# Function to add an item to the inventory
def add_item_to_inventory(driver, item):
    CONFIG["inventory"].append(parse_item_details(item.get_attribute('outerHTML')))
    saveConfig()

# Function to remove an item from the inventory
def remove_item_from_inventory(item_id):
    CONFIG["inventory"] = [item for item in CONFIG["inventory"] if item["id"] != item_id]
    saveConfig()

# Function to get player's health and mana
def get_health_mana(driver):
    try:
        wait = WebDriverWait(driver, 5)
        health_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".lifeMeter .meterBoxLabel")))
        mana_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".manaMeter .meterBoxLabel")))
        health_text = health_element.text.split(" / ")
        mana_text = mana_element.text.split(" / ")
        current_health = int(health_text[0])
        max_health = int(health_text[1])
        current_mana = int(mana_text[0])
        max_mana = int(mana_text[1])
        hp = (current_health / max_health) * 100
        mp = (current_mana / max_mana) * 100
        return {
            "hp": hp,
            "mp": mp
        }
    except Exception as e:
        write_to_terminal(f"Error: {e}")
        return None

# Function to find all monsters and their health
def get_monsters(driver):
    try:
        monsters = driver.find_elements(By.CSS_SELECTOR, ".mobArea .mob")
        monster_list = []
        
        for monster in monsters:
            name_element = monster.find_element(By.CSS_SELECTOR, ".meterBoxLabel")
            health_bar = monster.find_element(By.CSS_SELECTOR, ".lifeMeter .meterBoxProg")
            health_percentage = float(health_bar.get_attribute("style").split("width: ")[1].split("%")[0])
            monster_name = name_element.text

            write_to_terminal(f"Monster: {monster_name}, Health: {health_percentage}%")
            print(f"Monster: {monster_name}, Health: {health_percentage}%")
            monster_list.append({
                "element": monster,
                "name": monster_name,
                "health_percentage": health_percentage
            })

        return monster_list
    except Exception as e:
        write_to_terminal(f"Error: {e}")
        return []

# Function to switch to attack slot if health is above 70%
def attack_switch(driver, hp, mp):
    if hp > 60 or mp < 30:
        try:
            attack_slot = driver.find_element(By.CSS_SELECTOR, ".tbIcon.atkBox[slot='0']")
            if "sel" not in attack_slot.get_attribute("class"):
                attack_slot.click()
                write_to_terminal("Switched to attack slot.")
                print("Switched to attack slot.")
        except Exception as e:
            write_to_terminal(f"Error switching to attack slot: {e}")

# Function to attack a monster
def attack_monster(driver, monster):
    try:
        write_to_terminal(f"Attacking monster: {monster['name']}")
        actions = ActionChains(driver)
        actions.move_to_element(monster["element"]).click().perform()
    except Exception as e:
        write_to_terminal(f"Error attacking monster: {e}")

# Function to send keystrokes
def send_keystrokes(driver, keys):
    try:
        # Find an element to send keystrokes to (e.g., the body or a specific element)
        body = driver.find_element(By.TAG_NAME, "body")
        actions = ActionChains(driver)
        actions.move_to_element(body)
        
        # Send the specified keys
        actions.send_keys(keys).perform()
        
        write_to_terminal(f"Sent keystrokes: {keys}")
    except Exception as e:
        write_to_terminal(f"Error sending keystrokes: {e}")

# Function to go to town for healing
def town_heal(driver):
    try:
        try:
            town_button = driver.find_element(By.CSS_SELECTOR, ".abutGradBl.gradRed")  # Adjust selector as needed
            town_button.click()
        finally:
            print(" - Talking to Akara - ")
            write_to_terminal("Talking to Akara")
            time.sleep(5)  # Adjust healing time as needed
            health_mana_data = get_health_mana(driver)
            if health_mana_data:
                hp = health_mana_data['hp']
                mp = health_mana_data['mp']
                
                write_to_terminal(f"~Town Stats~")
                write_to_terminal(f"-HP: {hp}")
                write_to_terminal(f"-MP: {mp}")
                print(f"~Town Stats~")
                print(f"~HP: {hp}")
                print(f"-MP: {mp}")
                
                if hp < 100:
                    print("~~ Loop TownHeal ~~")
                    town_heal(driver)
                    return
        
    except Exception as e:
        write_to_terminal(f"Error going to town: {e}")

def fight_heal(driver,hp,mp):
    if hp < 50:
        if mp > 20: 
            send_keystrokes(driver,"R")
            time.sleep(1)
            #fight_heal(driver,hp,mp)
            send_keystrokes(driver,"Q")
            actions = ActionChains(driver).key_down(Keys.CONTROL).key_up(Keys.CONTROL).perform()
        else:
            send_keystrokes(driver,"Q")
            return
    else:
        send_keystrokes(driver,"Q")
        return

# Function to check if in town
def is_in_town(driver):
    try:
        town_elements = driver.find_elements(By.CSS_SELECTOR, ".townOption .townOLabel")
        for element in town_elements:
            if "Catacombs" in element.text:
                return True
        return False
    except Exception:
        return False

# Function to check if engage button is visible
def is_engage_button_visible(driver):
    try:
        engage_button = driver.find_element(By.CSS_SELECTOR, ".cataEngage")
        display_style = engage_button.get_attribute("style")
        if "display: block" in display_style:
            return True
        return False
    except Exception:
        print('CANT FIND ENGAGE BUTTON')
        return False

# Function to select catacombs when in town
def select_catacombs(driver):
    try:
        town_elements = driver.find_elements(By.CSS_SELECTOR, ".townOption .townOLabel")
        for element in town_elements:
            if "Catacombs" in element.text:
                element.click()
                time.sleep(2)  # Adjust as needed for the game to load
                send_keystrokes(driver, "a")
                send_keystrokes(driver, "a")
                return
    except Exception as e:
        write_to_terminal(f"Error selecting catacombs: {e}")

# Function to loot an item
def loot_item(driver, item):
    try:
        write_to_terminal(f"Looting item: {item['name']} with score: {item['score']}")
        item["element"].click()
        add_item_to_inventory(driver, item)
    except Exception as e:
        write_to_terminal(f"Error looting item: {e}")
        
        
#Too many monsters, reset dungeon
def resetDungeon(driver):
    try:
        print('-- TOO MANY MONSTERS -- resetDungeon() --')
        town_button = driver.find_element(By.CSS_SELECTOR, ".abutGradBl.gradRed")  
        town_button.click()
        time.sleep(2)
        controlButtons = driver.find_elements(By.CSS_SELECTOR, ".ctrlButtons .cp") 
        #print(f'controlButtons: {controlButtons}')
        for button in controlButtons:
            buttonName = button.get_attribute("src").split("/")[-1].replace(".svg", "")
            #print(f'buttonName: {buttonName}')
            if buttonName == 'iconGroup':
                button.click()
                time.sleep(2)
                groupTabs = driver.find_elements(By.CSS_SELECTOR, ".njRB") 
                #print(f'groupTabs: {groupTabs}')
                for tab in groupTabs:
                    print(f'tab: {tab}')
                    if tab.text == 'Create Group':
                        print('Create Group')
                        time.sleep(2)
                        tab.click()
                        time.sleep(2)
                        createGroupBtn = driver.find_element(By.CSS_SELECTOR, ".gpControls .gpJoin")  
                        createGroupBtn.click()
                        time.sleep(5)
                        button.click()
                        time.sleep(2)
                        
                        #click edit group tab
                        newGroupTabs = driver.find_elements(By.CSS_SELECTOR, ".njRB")
                        for newTab in newGroupTabs:
                            if newTab.text == 'Edit Group':
                                time.sleep(2)
                                newTab.click()
                                time.sleep(2)
                                ## LEAVE GROUP // EDIT GROUP BUTTONS
                                groupBtns = driver.find_elements(By.CSS_SELECTOR, ".gpControls .gpJoin")  
                                for btn in groupBtns:
                                    if btn.text == 'Leave Group':
                                        time.sleep(2)
                                        btn.click()
                                        time.sleep(180)
                        
        #Create Group
        #Leave Group
        
    finally:
        return
    
# Function to parse item drops and calculate their scores
def parse_and_score_drops(driver, drop_items):
    try:
        scored_items = []

        for item in drop_items:
            item_name_element = item.find_element(By.CSS_SELECTOR, "img")
            item_modifiers = item.find_elements(By.CSS_SELECTOR, ".ds2")
            print(f'item_name_element: {item_name_element}')
            print(f'item_modifiers: {item_modifiers}')
            hover_and_print_item_details(driver, item_name_element)
            
            item_name = item_name_element.get_attribute("src").split("/")[-1].replace(".svg", "")
            iLvl = [mod.text for mod in item_modifiers]
            
            item_score = calculate_item_score(item_name, iLvl)

            write_to_terminal(f"Item: {item_name}, Score: {item_score}")
            write_to_terminal(f"iLvl: {iLvl}")
            print(f"Item: {item_name}, Score: {item_score}")
            print(f"iLvl: {iLvl}")
            scored_items.append({
                "element": item,
                "name": item_name,
                "iLvl": iLvl,
                "score": item_score
            })

            if item_score > loot_threshold:
                loot_item(driver, item)

        return scored_items
    except Exception as e:
        write_to_terminal(f"Error parsing and scoring drops: {e}")
        return []



def is_leader(driver):
    return bool(driver.find_elements(By.CSS_SELECTOR, ".cName.gLeader"))

def engage_if_leader(driver):
    if is_leader(driver):
        print('Try find engage as leader')
        if is_engage_button_visible(driver):
            engage_button = driver.find_element(By.CSS_SELECTOR, ".cataEngage")  # Update selector as needed
            if engage_button:
                engage_button.click()

        # if whistle_var.get():
                # send_keystrokes(driver, "T")  # Assume T is the hotkey for whistle
                # write_to_terminal("Whistled.")
            # if engage_button:
                # engage_button.click()
                # write_to_terminal("Clicked engage button.")
            
            
            
        # SETUP SWITCH FOR WHISTLE

def wait_for_monsters():
    # Function that waits until monsters appear on the screen
    pass  # Implement based on game logic


def fight_based_on_role(driver, role):
    print(f'Fight Based On Role - Role: {role}')
    if role == 'healer':
        ensure_position(driver, 'posBack')
        heal_group_members(driver)
    elif role == 'tank':
        ensure_position(driver, 'posFront')
        attack_nearest_monster(driver)
    elif role == 'mage':
        ensure_position(driver, 'posBack')
        mage_attack_strategy(driver)
    elif role == 'dps':
        ensure_position(driver, 'posBack')
        attack_nearest_monster(driver)
    elif role == 'tankheal':
        ensure_position(driver, 'posFront')
        heal_group_members(driver)
    elif role == 'nohit':
        ensure_position(driver, 'posFront')

def heal_group_members(driver):
    # Example of healing group members
    group_members = driver.find_elements(By.CSS_SELECTOR, ".charObj")
    for member in group_members:
        health_text = member.find_element(By.CSS_SELECTOR, ".lifeMeter .meterBoxLabel").text
        current_health, max_health = map(int, health_text.split(' / '))
        if (current_health / max_health) * 100 < 50:
            # Assuming you have a healing skill assigned to 'R'
            send_keystrokes(driver, 'R')
           # member.click()
            write_to_terminal(f"Healed {member.find_element(By.CSS_SELECTOR, '.cName').text}")

def mage_attack_strategy(driver):
    global attack_counter
    attack_counter = attack_counter + 1
    
    if attack_counter % 2 == 0:
        spellAttack(driver,'R')
    else:
        attack_nearest_monster(driver)
    
def attack_nearest_monster(driver):
    global attack_counter
    attack_counter = attack_counter + 1
    print(f'Attack Counter: {attack_counter}')
    try:
        quickAttack(driver)
        monsters = get_monsters(driver)
        if len(monsters) > 4:
            print("Too many monsters")
            resetDungeon(driver)
            return
        
        send_keystrokes(driver, 'Q')
        if attack_counter % 17 == 0:
            actions = ActionChains(driver).key_down(Keys.CONTROL).key_up(Keys.CONTROL).perform()
        elif attack_counter % 19 == 0:
            actions = ActionChains(driver).key_down(Keys.ALT).key_up(Keys.ALT).perform()
        elif attack_counter % 13 == 0:
            actions = ActionChains(driver).key_down('R').key_up('R').perform()
        for monster in monsters:
            attack_monster(driver, monster)
            break
            
    except:
        print("couldnt attack monster")

def spellAttack(driver, key):
    try:
        #quickAttack(driver)
        monsters = get_monsters(driver)
        #if len(monsters) > 4:
            #resetDungeon(driver)
        
        send_keystrokes(driver, key)
        for monster in monsters:
            attack_monster(driver, monster)
            break
            
    except:
        print("couldnt attack monster")


def quickAttack(driver):
    try:
        monsters = get_monsters(driver)
        for monster in monsters:
            attack_monster(monster)
            break
    except:
        print("Quick Attack Failed")


def automate_fighting(driver):
    global fighting, fight_state, role
    write_to_terminal(f"Fighting: {fighting}")
    write_to_terminal(f"Fight State: {fight_state}")
    #update_overlay_position()
    
    if fighting:
        try:
            isLeader = is_leader(driver)
            print(f'Is Leader: {isLeader}')
            if is_in_town(driver):
                select_catacombs(driver)
        
            checkHealth(driver)
                #Print group health/mana data
                
            if not isLeader:
                wait_for_monsters()
            else:
                engage_if_leader(driver)
                
            fight_based_on_role(driver, role)
            print('Check Items')
            drop_items = driver.find_elements(By.CSS_SELECTOR, ".dropItemsBox .itemBox")
            if drop_items:
                print('Found Items')
                parse_and_score_drops_new(driver, drop_items)
        except:
            print('In Automate Fighting - Fighting Exception')
        overlay.after(1000, lambda: automate_fighting(driver))  # Adjust delay as needed

def checkHealth(driver):
    try:
        health_mana_data = get_health_mana(driver)
        
        if health_mana_data:
            hp = health_mana_data['hp']
            mp = health_mana_data['mp']
            
            write_to_terminal(f"-HP: {hp}")
            write_to_terminal(f"-MP: {mp}")
            print(f"-HP: {hp}")
            print(f"-MP: {mp}")
            
            if hp < 40:
                print("Fight: ~> Town Heal <~")
                write_to_terminal("Fight: ~> Town Heal <~")
                town_heal(driver)
                
            #if hp < 60:
                #fight_heal(driver, hp, mp)
            #if hp > 60 or mp < 30:
                #attack_switch(driver, hp, mp)
            
    except Exception as e:
        print(f"Error in checkHealthAndReact: {e}")
    
# Function to automate fighting
# def automate_fighting(driver):
    # global fighting, fight_state
    # write_to_terminal(f"Fighting: {fighting}")
    # update_overlay_position()
    # if fighting:
        # if is_in_town(driver):
            # select_catacombs(driver)

        # health_mana_data = get_health_mana(driver)
        # if health_mana_data:
            # current_health = health_mana_data['current_health']
            # max_health = health_mana_data['max_health']
            # current_mana = health_mana_data['current_mana']
            # max_mana = health_mana_data['max_mana']
            
            # hp = (current_health / max_health) * 100
            # mp = (current_mana / max_mana) * 100
            # write_to_terminal(f"-HP: {hp}")
            # print(f"-HP: {hp}")
            # write_to_terminal(f"-MP: {mp}")
            # print(f"-MP: {mp}")
            
            # if hp < 40:
                # print("Fight: ~> Town Heal <~")
                # town_heal(driver)
            # if hp < 60:
                # fight_heal(driver, hp, mp)
            # if hp > 60 or mp < 30:
                # attack_switch(driver, hp, mp)
        
        # drop_items = driver.find_elements(By.CSS_SELECTOR, ".dropItemsBox .itemBox")
        # if drop_items:
            # parse_and_score_drops(driver, drop_items)
            
        # monsters = get_monsters(driver)
        # if len(monsters) > 4:
            # resetDungeon(driver)
        # if not monsters:
            # if is_engage_button_visible(driver):
                # engage_button = driver.find_element(By.CSS_SELECTOR, ".cataEngage")
                # if whistle_var.get():
                    # send_keystrokes(driver, "T")  # Assume T is the hotkey for whistle
                    # write_to_terminal("Whistled.")
                # if engage_button:
                    # engage_button.click()
                    # write_to_terminal("Clicked engage button.")
            # else:
                # send_keystrokes(driver, "T")
                
        # for monster in monsters:
            # if monster["health_percentage"] > 0:
                # attack_monster(driver, monster)
                # break

        # # Schedule next fight action
        # overlay.after(1000, lambda: automate_fighting(driver))  # Adjust delay as needed

# Function to start fighting
def fight():
    global fighting, role
    
    driver = setup_browser()
    fighting = True
    print("Get Character Config")
    getCharacter(driver)
    role = CONFIG['class']
    
    # Scan inventory and equipment at the start
    #update_character_json(driver)
    
    write_to_terminal("Fight!... ")
    automate_fighting(driver)


# Function to stop automation
def stop_automation():
    global fighting
    fighting = False
    write_to_terminal("Automation stopped by hotkey...")
    os._exit(0)

# Set up the GUI
overlay = tk.Tk()
overlay.title("Slash Hustler")
overlay.geometry("400x500+1450+530")
#overlay.attributes('-topmost', True)
overlay.attributes('-alpha', 0.7)
overlay.overrideredirect(True)

fight_button = tk.Button(overlay, bg='black', fg='white', font=('exocet', 9), text="Fight", command=fight)
fight_button.pack()

stop_button = tk.Button(overlay, bg='black', fg='white', font=('exocet', 9), text="Stop", command=stop_automation)
stop_button.pack()

whistle_var = tk.BooleanVar(value=False)  # Set initial value to False
whistle_checkbox = tk.Checkbutton(overlay, text="Whistle", variable=whistle_var, bg='black', fg='white', font=('exocet', 9))
whistle_checkbox.pack()

terminal_output = tk.Text(overlay, bg='black', fg='white', font=('exocet', 9), wrap='word')
terminal_output.pack(expand=True, fill='both')

#sys.stdout = StdoutRedirector(terminal_output)

keyboard.add_hotkey('+', stop_automation)



# Start the monitoring thread (Updating Overlay Position) (Auto Minimize)
thread = threading.Thread(target=update_overlay_position)
thread.daemon = True
thread.start()

overlay.mainloop()
