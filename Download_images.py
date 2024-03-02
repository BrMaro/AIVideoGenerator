import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from tqdm import tqdm
import time
import re
import cohere

options = Options()
options.add_experimental_option("detach", True)
options.add_argument("user-data-dir=C:\\Users\\Techron\\AppData\\Local\\Google\\Chrome\\User Data")
driver = webdriver.Chrome(options=options)
url = "https://app.leonardo.ai/"
driver.get(url)
driver.implicitly_wait(20)

script="The time THOR cosplayed and GOT MARRIED?!!Remember when THOR cosplayed.Yeah, you had that right,THOR’s Mjolnir was stolen by the Thrym, wonder how they carried, anywho, the giants offered to return the hammer in exchange for Freya’s hand in marriage, So of course the logical thing to do was to dress up as Freya and get married and it worked During the party, Thor grabbed Mjolnir and slaughtered all the giants and ogres there. From that day on, pretty sure all the giants………"
IMAGE_NUMBER = 20
IMAGE_PER_PROMPT = 1
FOLDER_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator\\Images"
FILE_TYPE = ".jpg"
timeoutTime = 60
wait = WebDriverWait(driver,timeoutTime)


def set_aspect_ratio():
    select_element = driver.find_element(By.XPATH,"//select[@id='field-:r7a:']")
    select = Select(select_element)
    select.select_by_value("7")


def clean_filename(filename):
    pattern = r'[\\/:"*?<>|]|\.{2,}|[<>]|\s+$|^\.|[ ]+$'

    cleaned_filename = re.sub(pattern, '_', filename)

    cleaned_filename = cleaned_filename.strip()

    if not cleaned_filename:
        cleaned_filename = 'unnamed_file'

    return cleaned_filename


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


def generate_image_prompts(script):
    with open('API_KEY.txt',"r") as key:
        API_KEY = key.read()
    co = cohere.Client(API_KEY)

    response = co.generate(
        prompt= f"create {IMAGE_NUMBER} vivid descriptive image scenes from:{script}"
    )
    return response

print(generate_image_prompts(script))



def pass_image_prompts_to_ai(promptsArr):
    driver.find_element(By.XPATH,"//p[text()='Image Generation']").click() # image generation tab
    driver.find_element(By.XPATH,"//textarea[@class='chakra-textarea css-jj5ykg']").click() # i
    driver.find_element(By.XPATH,f"(//div[@class='css-lrke8r'])[{IMAGE_PER_PROMPT}]").click()


    for prompt in promptsArr:

        user_input = driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']")
        user_input.click()
        user_input.send_keys(Keys.CONTROL + 'a')
        user_input.send_keys(Keys.DELETE)
        user_input.send_keys(prompt)
        driver.find_element(By.XPATH,"//button[@class='chakra-button css-102okvd']").click() # Start generation

        image_locator = (By.XPATH, f'//img[@alt="{prompt}"]')
        image = wait.until(EC.presence_of_element_located(image_locator))

        img_src = image.get_attribute("src")
        prompt = image.get_attribute("alt")
        download_image(img_src, f"{FOLDER_PATH}\\{clean_filename(prompt[:80])}.{FILE_TYPE}")

    driver.quit()

# pass_image_prompts_to_ai(["Scene 2:Setting: Wedding Ceremony Grounds Characters:Thor (Freya disguise): Trying to maintain composure.Thrym: Smirking, thinking he has outsmarted the Asgardians.Odin: Watching from his throne with a mix of amusement and concern.Loki: Sneaking around in the background, planning mischief.Description: The ceremony is about to begin, with Thor and Thrym facing each other. Odin observes from his throne, and Loki lurks in the shadows, ready to cause chaos."])



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
