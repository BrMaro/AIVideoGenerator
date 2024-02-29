import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
from tqdm import tqdm
import time

options = Options()
options.add_experimental_option("detach", True)
options.add_argument("user-data-dir=C:\\Users\\Techron\\AppData\\Local\\Google\\Chrome\\User Data")
driver = webdriver.Chrome(options=options)
url = "https://app.leonardo.ai/"
driver.get(url)
driver.implicitly_wait(10)

script="The time THOR cosplayed and GOT MARRIED?!!Remember when THOR cosplayed.Yeah, you had that right,THOR’s Mjolnir was stolen by the Thrym, wonder how they carried, anywho, the giants offered to return the hammer in exchange for Freya’s hand in marriage, So of course the logical thing to do was to dress up as Freya and get married and it worked During the party, Thor grabbed Mjolnir and slaughtered all the giants and ogres there. From that day on, pretty sure all the giants………"
IMAGE_NUMBER = 20
IMAGE_PER_PROMPT = 1
FOLDER_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator\\Images"
FILE_TYPE = ".jpg"

def download_image(imgUrl, filepath):
    try:
        response = requests.get(imgUrl, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192  # Adjust as needed

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as file, tqdm(
                desc=os.path.basename(filepath),
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    file.write(chunk)
                    bar.update(len(chunk))
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created successfully.")
    else:
        print(f"Folder '{folder_name}' already exists. Skipping creation.")


def get_image_prompts_from_script(script):
    prompt_text = f"Generate {IMAGE_NUMBER} image scene prompts making sure to encapsulate the environment and the theme for the following script:{script}"
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get("https://chat.openai.com/")
    driver.implicitly_wait(10)
    input_form = driver.find_element(By.ID,"prompt-textarea")
    input_form.send_keys(prompt_text)
    input_form.send_keys(Keys.RETURN)
    response = driver.find_elements(By.XPATH,"//div[@class='w-full text-token-text-primary']")
    time.sleep(10)
    driver.switch_to.window((driver.window_handles[0]))
    return (response[-1].text)

# print(get_image_prompts_from_script(script))


def pass_image_prompts_to_ai(promptsArr):
    driver.find_element(By.XPATH,"//p[text()='Image Generation']").click() # image generation tab
    driver.find_element(By.XPATH,"//textarea[@class='chakra-textarea css-jj5ykg']").click() # i
    driver.find_element(By.XPATH,f"(//div[@class='css-lrke8r'])[{IMAGE_PER_PROMPT}]").click()

    for prompt in promptsArr:
        user_input = driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']")
        user_input.click()
        user_input.send_keys(prompt)
        driver.find_element(By.XPATH,"//button[@class='chakra-button css-102okvd']")
        image_panel = driver.find_element(By.XPATH,"//div[@class='css-1eiwtsh']")
        images = image_panel.find_elements(By.TAG_NAME,"img")
        img_src = images[0].get_attribute("src")
        prompt = images[0].get_attribute("alt")
        time.sleep(10)
        download_image(img_src, f"{FOLDER_PATH}\\{prompt[:40]}.{FILE_TYPE}")

pass_image_prompts_to_ai(["Amidst the vibrant, celestial realm of Asgard, a colossal banquet hall sprawls beneath a kaleidoscope sky of swirling cosmic hues. Glistening pillars of iridescent crystal hold aloft the celestial ceiling, casting a resplendent glow over the gathering. The air is filled with the enchanting melodies of unseen celestial beings, harmonizing in celestial tunes.","At the center of the opulent hall stands a radiant throne, adorned with luminous gemstones and intricate runes. A majestic feast table stretches across the expanse, laden with ambrosial delights and exotic fruits from realms unknown. Guests, a mix of gods and ethereal beings, mingle in jubilant celebration, their radiant garments flowing like liquid rainbows."])



def main():
    try:
        driver.implicitly_wait(10)
        # driver.find_element(By.XPATH, "(//button[text()='Architecture'])[3]").click()

        create_folder(FOLDER_PATH)

        image_div = driver.find_element(By.XPATH, "//div[@class='css-mveqkt']")

        images = image_div.find_elements(By.TAG_NAME, "img")

        image_dictionary = {}
        # Key(IMAGE PATH),Value:(PROMPT)
        for img in images[:IMAGE_NUMBER]:
            src = img.get_attribute("src")
            prompt = img.get_attribute("alt")
            image_dictionary[src] = prompt
            download_image(src, f"{FOLDER_PATH}\\{prompt[:40]}.{FILE_TYPE}")
    except Exception as e:
        print(e)
