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



IMAGE_NUMBER = 20
IMAGE_PER_PROMPT = 1
FOLDER_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator\\Images"
FILE_TYPE = ".jpg"
timeoutTime = 60


def get_script():
    with open('script.txt','r') as file:
        content = file.read()
        return content


def initialize_selenium():
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("user-data-dir=C:\\Users\\Techron\\AppData\\Local\\Google\\Chrome\\User Data")
    driver = webdriver.Chrome(options=options)
    return driver


def set_aspect_ratio(driver):
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


def generate_image_prompts_from_script(script):
    with open('API_KEY.txt',"r") as key:
        API_KEY = key.read()
    co = cohere.Client(API_KEY)

    response = co.generate(
        prompt= f"create {IMAGE_NUMBER} vivid descriptive image scenes from:{script}"
    )
    return response


def clean_api_response(response):
    response = str(response)
    matches = re.findall(r'\s+(\d+\.\s.*?)\n', response, re.DOTALL)

    # Create an array to store the individual texts
    texts_array = []

    # Iterate through matches and append to the array
    for match in matches:
        texts_array.append(match.strip())

    # Print or use the array as needed
    return texts_array


def pass_image_prompts_to_ai(driver,promptsArr):
    url = "https://app.leonardo.ai/"
    driver.get(url)
    driver.implicitly_wait(20)

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
        image = WebDriverWait(driver, timeoutTime).until(EC.presence_of_element_located(image_locator))

        img_src = image.get_attribute("src")
        prompt = image.get_attribute("alt")
        download_image(img_src, f"{FOLDER_PATH}\\{clean_filename(prompt[:80])}.{FILE_TYPE}")

    driver.quit()


def main():
    script = get_script()

    driver = initialize_selenium()

    driver.implicitly_wait(10)

    create_folder(FOLDER_PATH)

    response = generate_image_prompts_from_script(script)


    arr = clean_api_response(response)
    print(arr)
    pass_image_prompts_to_ai(driver,arr)





main()
