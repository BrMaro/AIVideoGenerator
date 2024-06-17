from moviepy.editor import *
import os
from dotenv import load_dotenv
from tqdm import tqdm
import numpy as np
from PIL import Image
from moviepy.config import change_settings
import captacity
from tiktokvoice import tts
from pydub import AudioSegment

load_dotenv()

# Load Env variables
PROJECT_PATH = os.getenv("PROJECT_PATH")
IMAGE_FILE_TYPE = os.getenv('IMAGE_FILE_TYPE')
FONT = os.getenv("FONT")
IMAGEMAGICK_FILE_PATH = os.getenv("IMAGEMAGICK_FILE_PATH")
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_FILE_PATH})

IMAGE_FOLDER_PATH = os.path.join(PROJECT_PATH, "Images")
SUBTITLE_FILE_PATH = os.path.join(PROJECT_PATH, "subtitles.txt")

HEIGHT = 1920
WIDTH = 1080
DURATION_PER_IMAGE = 2
language = 'en'


def get_script():
    with open('script.txt', 'r', encoding='utf-8') as file:
        content = file.read()
        return content


def get_image_files(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_FILE_TYPE)]
    print("Image files collected")
    return image_files


def crop_image_to_aspect_ratio(image_path, target_width, target_height):
    try:
        original_image = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None

    # Get the original dimensions
    original_width, original_height = original_image.size

    # Calculate the target aspect ratio
    target_aspect_ratio = target_width / target_height

    # Calculate the new dimensions to crop to
    if original_width / original_height > target_aspect_ratio:
        # Crop the width
        new_width = int(original_height * target_aspect_ratio)
        new_height = original_height
        x_offset = (original_width - new_width) // 2
        y_offset = 0
    else:
        # Crop the height
        new_width = original_width
        new_height = int(original_width / target_aspect_ratio)
        x_offset = 0
        y_offset = (original_height - new_height) // 2

    # Crop the image
    cropped_image = original_image.crop((x_offset, y_offset, x_offset + new_width, y_offset + new_height))

    # Resize the image to the target size
    resized_image = cropped_image.resize((target_width, target_height), Image.ANTIALIAS)

    return resized_image


def crop_image(img_file):
    image_path = os.path.join(IMAGE_FOLDER_PATH, img_file)
    img = crop_image_to_aspect_ratio(image_path, WIDTH, HEIGHT)

    if img is None:
        return None

    # Convert PIL Image to NumPy array
    img_array = np.array(img)

    # Create ImageClip from NumPy array
    img_clip = ImageClip(img_array)

    return img_clip

def add_voice(script):
    voice = "en_us_006"
    tts(script, voice, "script.mp3")


def speed_up_audio(audio_path, speed_factor):
    audio = AudioSegment.from_file(audio_path)
    sped_up_audio = audio.speedup(playback_speed=speed_factor)
    sped_up_audio.export("script_sped_up.mp3", format="mp3")


def add_subtitles(video_file):
    captacity.add_captions(
        print_info=True,

        video_file=video_file,
        output_file=f"Captioned_{video_file}",

        font=FONT,
        font_size=60,
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

    add_voice(script)
    speed_up_audio("script.mp3", 1.01)

    audio_clip = AudioFileClip('script_sped_up.mp3')
    audio_duration = audio_clip.duration

    image_files = get_image_files(image_folder)

    num_images = len(image_files)
    duration_per_image = audio_duration / num_images

    print(f"Expected video length: {audio_duration:.2f} seconds")

    cropped_images = []
    for image_file in tqdm(image_files, desc="Cropping images", unit="image"):
        img_clip = crop_image(image_file)
        if img_clip is not None:
            img_clip = img_clip.set_duration(duration_per_image).set_position(("center", "center"))
            cropped_images.append(img_clip)

    if not cropped_images:
        raise ValueError("No valid images to create video")

    final_clip = concatenate_videoclips(cropped_images, method='compose')
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
    add_subtitles(output_path)

    if os.path.exists("script.mp3"):
        os.remove("script.mp3")
        os.remove("script_sped_up.mp3")
    if os.path.exists(SUBTITLE_FILE_PATH):
        os.remove(SUBTITLE_FILE_PATH)


create_video(IMAGE_FOLDER_PATH, 'output_video.mp4', fps=30)
