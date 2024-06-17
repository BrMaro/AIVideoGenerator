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
from dotenv import load_dotenv
from tqdm import tqdm
import re
import cohere
import time

load_dotenv()

IMAGE_NUMBER = 20
IMAGE_PER_PROMPT = 1
PROJECT_PATH = os.getenv("PROJECT_PATH")
IMAGE_FOLDER_PATH = os.path.join(PROJECT_PATH, "Images")

IMAGE_FILE_TYPE = os.getenv("IMAGE_FILE_TYPE")
timeoutTime = 60


def get_script():
    start_time = time.time()
    with open('script.txt', 'r', encoding='utf-8') as file:
        content = file.read()
    print(f"Loaded script in {time.time() - start_time:.2f} seconds")
    return content


def initialize_selenium():
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("user-data-dir=C:\\Users\\Techron\\AppData\\Local\\Google\\Chrome\\User Data")
    driver = webdriver.Chrome(options=options)
    return driver


def clean_filename(filename):
    pattern = r'[\\/:"*?<>|]|\.{2,}|[<>]|\s+$|^\.|[ ]+$'

    cleaned_filename = re.sub(pattern, '_', filename)

    cleaned_filename = cleaned_filename.strip()

    if not cleaned_filename:
        cleaned_filename = 'unnamed_file'

    return cleaned_filename


def download_image(imgUrl, filepath):
    start_time = time.time()
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
        print(f"Folder '{folder_name}' already exists. ")


def generate_image_prompts_from_script(script):
    start_time = time.time()
    print("Accessing Cohere API")
    API_KEY = os.getenv('COHERE_API_KEY')
    co = cohere.Client(API_KEY)

    response = co.generate(
        prompt=f"""Generate {IMAGE_NUMBER} numbered distinct, vivid visual scenes that encapsulate
                Consistent Character Name:
                Ensure the character name remains consistent throughout all scenes.
                Character Positioning:
                Specify the position of the character in each scene (e.g., background, midground, foreground).
                Character's Facial Expression:
                Describe the character's facial expression to convey the appropriate emotions (e.g., happy, sad, surprised).
                Character's Clothing:
                Provide details about the character's clothing, including colors, styles, and any unique features to maintain consistency.
                Scene Setting:
                Describe the setting of each scene in detail (e.g., urban cityscape, rural countryside, cozy interior).
                Lighting and Atmosphere:
                Specify the lighting conditions (e.g., bright daylight, dim evening, dramatic shadows) and overall atmosphere (e.g., tense, cheerful, mysterious).
                Background Elements:
                Include details about the background elements (e.g., trees, buildings, mountains) to give depth to the scene.
                Foreground Elements:
                Mention any objects or elements in the foreground that interact with the character or add context to the scene.
                Action and Movement:
                Describe any actions or movements the character is making (e.g., running, sitting, talking).
                Interaction with Other Characters:
                If there are other characters, describe their interactions with the main character and their expressions and positions.
                Props and Accessories:
                Include details about any props or accessories the character is using or holding (e.g., books, weapons, tools).
                Emotional Tone:
                Specify the emotional tone of the scene (e.g., joyful, melancholic, tense) to guide the AI in capturing the right mood.
                Environment Details:
                Provide specifics about the environment (e.g., weather conditions, time of day, season).
                Color Palette:
                Suggest a color palette for the scene to ensure visual consistency and mood setting.
                Camera Angle and Perspective:
                Describe the camera angle and perspective (e.g., close-up, wide shot, bird's eye view) to influence the composition of the scene.
                
                 Here is the SCRIPT:\n{script}"""
    )
    print(f"Generated image prompts from script in {time.time() - start_time:.2f} seconds")
    return response


def clean_api_response(response):
    start_time = time.time()
    response = str(response)
    matches = re.findall(r'\s+(\d+\.\s.*?)\n', response, re.DOTALL)
    texts_array = []
    for match in matches:
        match = re.sub(r"'", r"", match)
        texts_array.append(match.strip())
    print(f"Cleaned API response in {time.time() - start_time:.2f} seconds")
    return texts_array


def pass_image_prompts_to_ai(driver, promptsArr):
    start_time = time.time()
    url = "https://app.leonardo.ai/"
    driver.get(url)
    driver.implicitly_wait(20)

    #image preferences
    driver.find_element(By.XPATH, "//p[text()='Image Generation']").click()  # image generation tab
    driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']").click()  # i

    # Wait for the user to press Enter
    input("Press Enter to continue...")

    for prompt in promptsArr:
        user_input = driver.find_element(By.XPATH, "//textarea[@class='chakra-textarea css-jj5ykg']")
        user_input.click()
        user_input.send_keys(Keys.CONTROL + 'a')
        user_input.send_keys(Keys.DELETE)
        user_input.send_keys(prompt)
        driver.find_element(By.XPATH, "//button[@class='chakra-button css-6bvv2d']").click()  # Start generation

        image_locator = (By.XPATH, f"//img[@alt='{prompt}']")
        image = WebDriverWait(driver, timeoutTime).until(EC.presence_of_element_located(image_locator))

        img_src = image.get_attribute("src")
        prompt = image.get_attribute("alt")
        download_image(img_src, f"{IMAGE_FOLDER_PATH}\\{clean_filename(prompt[:80])}.{IMAGE_FILE_TYPE}")

    print(f"Completed processing all prompts in {time.time() - start_time:.2f} seconds")
    driver.quit()


def main():
    start_time = time.time()
    print("\nLoading..................\n\n")
    try:
        script = get_script()

        create_folder(IMAGE_FOLDER_PATH)

        response = generate_image_prompts_from_script(script)

        arr = clean_api_response(response)

        driver = initialize_selenium()

        driver.implicitly_wait(20)

        pass_image_prompts_to_ai(driver, arr)

    except SessionNotCreatedException as e:
        print(f"{e}")

    print(f"Script completed in {time.time() - start_time:.2f} seconds")


main()
