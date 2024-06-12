from moviepy.editor import *
from moviepy.video.fx.resize import resize
from moviepy.video.fx.all import *
import random
import os
from dotenv import load_dotenv
from tqdm import tqdm
import numpy as np
from PIL import Image
from gtts import gTTS
import re
from moviepy.config import change_settings
import captacity

load_dotenv()

# Load Env variables
PROJECT_PATH = os.getenv("PROJECT_PATH")
IMAGE_FILE_TYPE = os.getenv('IMAGE_FILE_TYPE')
FONT = os.getenv("FONT")
IMAGEMAGICK_FILE_PATH = os.getenv("IMAGEMAGICK_FILE_PATH")
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_FILE_PATH})

IMAGE_FOLDER_PATH = os.path.join(PROJECT_PATH, "Images")
SUBTITLE_FILE_PATH = os.path.join(PROJECT_PATH, "subtitles.txt")

HEIGHT = 1080
ASPECT_RATIO = 9 / 16
WIDTH = round(HEIGHT * ASPECT_RATIO)
DURATION_PER_IMAGE = 2
language = 'en'


def get_script():
    with open('script.txt', 'r', encoding='utf-8') as file:
        content = file.read().upper()
        return content


def get_image_files(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_FILE_TYPE)]
    print("Image files collected")
    return image_files


def resize_image_with_aspect_ratio(image_path, target_width, target_height):
    original_image = Image.open(image_path)

    # Get the original aspect ratio
    original_width, original_height = original_image.size
    original_aspect_ratio = original_width / original_height

    # Calculate the new dimensions while maintaining the aspect ratio
    if original_aspect_ratio > target_width / target_height:
        new_width = int(target_width)
        new_height = int(target_width / original_aspect_ratio)
    else:
        new_width = int(target_height * original_aspect_ratio)
        new_height = int(target_height)

    # Resize the image
    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return resized_image


def resize_image(img_file):
    image_path = os.path.join(IMAGE_FOLDER_PATH, img_file)
    img = resize_image_with_aspect_ratio(image_path, WIDTH, HEIGHT)

    # Convert PIL Image to NumPy array
    img_array = np.array(img)

    # Create ImageClip from NumPy array
    img_clip = ImageClip(img_array)

    return img_clip


def add_sound(script):
    if not os.path.exists("script.mp3"):
        mysound = gTTS(text=script, lang=language)
        mysound.save("script.mp3")
    else:
        print("Script file already exists")


def add_subtitles(video_file, ):
    captacity.add_captions(
        print_info=True,

        video_file=video_file,
        output_file=f"Captioned_{video_file}",

        font="C:\\Windows\\Fonts\\Arial.ttf",
        font_size=80,
        font_color="white",

        stroke_width=1,
        stroke_color="black",

        shadow_strength=5.0,
        shadow_blur=0.5,

        highlight_current_word=True,
        word_highlight_color="red",

        line_count=1,
    )


def create_video(image_folder, output_path, fps=24):
    script = get_script()
    add_sound(script)
    audio_clip = AudioFileClip('script.mp3')
    audio_duration = audio_clip.duration
    image_files = get_image_files(image_folder)

    num_images = len(image_files)
    duration_per_image = audio_duration / num_images

    print(f"Expected video length: {audio_duration:.2f} seconds")

    resized_images = [resize_image(image_file).set_duration(duration_per_image).set_position(("center", "center"))
                      for image_file in tqdm(image_files, desc="Resizing images", unit="image")]

    for img_clip in resized_images:
        img_clip = img_clip.fx(vfx.fadeout, 0.5).fx(vfx.fadein, 0.5)

    final_clip = concatenate_videoclips(resized_images, method='compose')
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
    add_subtitles('output_video.mp4')

    # if os.path.exists("script.mp3"):
    #     os.remove("script.mp3")
    if os.path.exists(SUBTITLE_FILE_PATH):
        os.remove(SUBTITLE_FILE_PATH)


create_video(IMAGE_FOLDER_PATH, 'output_video.mp4', fps=30)
