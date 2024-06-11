import os
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
import requests
import psutil
from dotenv import load_dotenv
from tqdm import tqdm
import time
import re
import cohere

load_dotenv()

IMAGE_NUMBER = 20
IMAGE_PER_PROMPT = 1
FOLDER_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator\\Images"
IMAGE_FILE_TYPE = os.getenv("IMAGE_FILE_TYPE")
timeoutTime = 60


def get_script():
    with open('script.txt', 'r', encoding='utf-8') as file:
        content = file.read()
        return content


def initialize_selenium():
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("user-data-dir=C:\\Users\\Techron\\AppData\\Local\\Google\\Chrome\\User Data")
    driver = webdriver.Chrome(options=options)
    return driver


def set_aspect_ratio(driver):
    select_element = driver.find_element(By.XPATH, "//select[@id='field-:r7a:']")
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
        block_size = 8192

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


def generate_image_prompts_from_script(script):
    print("Accessing Cohere API")
    API_KEY = os.getenv('COHERE_API_KEY')
    co = cohere.Client(API_KEY)

    response = co.generate(
        prompt=f"Generate {IMAGE_NUMBER} numbered different vivid and descriptive visual scenes inspired by the script provided. Ensure each scene captures the essence of the setting,environment and mood. Emphasize detailed surroundings and character interactions to bring the narrative to life. Aim to depict key moments and emotions portrayed in the script, highlighting dynamic visuals that evoke a strong sense of atmosphere and storytelling. Make sure to use consistent naming and also describe clothing where necesary to maintain character consistency. Here is the provided SCRIPT: \n{script}"
    )
    return response


def clean_api_response(response):
    response = str(response)
    print(response)
    matches = re.findall(r'\s+(\d+\.\s.*?)\n', response, re.DOTALL)

    texts_array = []

    for match in matches:
        match = re.sub(r"'", r"", match)
        texts_array.append(match.strip())
        print(match.strip())

    print("Cleaned API Response")
    return texts_array


def pass_image_prompts_to_ai(driver, promptsArr):
    url = "https://app.leonardo.ai/"
    driver.get(url)
    driver.implicitly_wait(20)

    #image preferences
    driver.find_element(By.XPATH, "//p[text()='Image Generation']").click()  # image generation tab
    driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']").click()  # i

    for prompt in promptsArr:
        user_input = driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']")
        user_input.click()
        user_input.send_keys(Keys.CONTROL + 'a')
        user_input.send_keys(Keys.DELETE)
        user_input.send_keys(prompt)
        driver.find_element(By.XPATH, "//button[@class='chakra-button css-102okvd']").click()  # Start generation

        image_locator = (By.XPATH, f"//img[@alt='{prompt}']")
        image = WebDriverWait(driver, timeoutTime).until(EC.presence_of_element_located(image_locator))

        img_src = image.get_attribute("src")
        prompt = image.get_attribute("alt")
        download_image(img_src, f"{FOLDER_PATH}\\{clean_filename(prompt[:80])}.{IMAGE_FILE_TYPE}")

    driver.quit()


def main():
    print("\nRUNNING\n\n")
    try:
        script = get_script()

        driver = initialize_selenium()

        driver.implicitly_wait(10)

        create_folder(FOLDER_PATH)

        response = generate_image_prompts_from_script(script)

        arr = clean_api_response(response)
        pass_image_prompts_to_ai(driver, arr)

    except SessionNotCreatedException as e:
        print(f"{e}")


main()
