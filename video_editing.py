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
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import random
from moviepy.decorators import add_mask_if_none, requires_duration
import cohere
import time
import re

load_dotenv()

# Load Env variables
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
IMAGE_FILE_TYPE = os.getenv('IMAGE_FILE_TYPE')
FONT = os.getenv("FONT")
IMAGEMAGICK_FILE_PATH = os.getenv("IMAGEMAGICK_FILE_PATH")
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_FILE_PATH})

API_KEY = os.getenv('COHERE_API_KEY')

IMAGE_FOLDER_PATH = os.path.join(PROJECT_PATH, "Images")
SUBTITLE_FILE_PATH = os.path.join(PROJECT_PATH, "subtitles.txt")

HEIGHT = 1920
WIDTH = 1080
DURATION_PER_IMAGE = 2
language = 'en'


# Define transitioins
@requires_duration
@add_mask_if_none
def crossfadein(clip, duration):
    clip.mask.duration = clip.duration
    new_clip = clip.copy()
    new_clip.mask = clip.mask.fx(fadein, duration)
    return new_clip


@requires_duration
@add_mask_if_none
def crossfadeout(clip, duration):
    clip.mask.duration = clip.duration
    new_clip = clip.copy()
    new_clip.mask = clip.mask.fx(fadeout, duration)
    return new_clip


def slide_in(clip, duration, side):
    w, h = clip.size
    pos_dict = {
        "left": lambda t: (min(0, w * (t / duration - 1)), "center"),
        "right": lambda t: (max(0, w * (1 - t / duration)), "center"),
        "top": lambda t: ("center", min(0, h * (t / duration - 1))),
        "bottom": lambda t: ("center", max(0, h * (1 - t / duration))),
    }

    return clip.set_position(pos_dict[side])


def slide_out(clip, duration, side):
    w, h = clip.size
    ts = clip.duration - duration  # start time of the effect.
    pos_dict = {
        "left": lambda t: (min(0, w * (-(t - ts) / duration)), "center"),
        "right": lambda t: (max(0, w * ((t - ts) / duration)), "center"),
        "top": lambda t: ("center", min(0, h * (-(t - ts) / duration))),
        "bottom": lambda t: ("center", max(0, h * ((t - ts) / duration))),
    }

    return clip.set_position(pos_dict[side])


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


def crop_video_to_aspect_ratio(video_clip, target_width, target_height):
    original_width, original_height = video_clip.size
    target_aspect_ratio = target_width / target_height

    # Calculate the new dimensions to crop to
    if original_width / original_height > target_aspect_ratio:
        # Crop the width
        new_width = int(original_height * target_aspect_ratio)
        x_offset = (original_width - new_width) // 2
        y_offset = 0
        crop_clip = video_clip.crop(x1=x_offset, y1=y_offset, x2=x_offset + new_width, y2=original_height)
    else:
        # Crop the height
        new_height = int(original_width / target_aspect_ratio)
        x_offset = 0
        y_offset = (original_height - new_height) // 2
        crop_clip = video_clip.crop(x1=x_offset, y1=y_offset, x2=original_width, y2=y_offset + new_height)

    return crop_clip.resize((target_width, target_height))


def add_voice(script):
    voice = "en_us_006"
    tts(script, voice, "script.mp3")


def speed_up_audio(audio_path, speed_factor):
    audio = AudioSegment.from_file(audio_path)
    sped_up_audio = audio.speedup(playback_speed=speed_factor)
    sped_up_audio.export("script_sped_up.mp3", format="mp3")


def get_moods_from_script(script):
    start_time = time.time()
    print("Accessing Cohere API")
    co = cohere.Client(API_KEY)

    response = co.generate(
        prompt=f"""Outline 3 numbered,distinct moods that the following script tries to embody.P.S. just name the moods nothing ele. 
        Choose from the following: Sadness, Happiness, Loneliness, Hopefulness, Fear, Joy,Amusement, Eroticism, Beauty, Relaxation, Triumph, Defiance, Pumped up,
        Here is the script:\n{script}"""
    )
    print(f"Moods in the script analyzed in {time.time() - start_time:.2f} seconds")

    text_response = response[0].text
    pattern = r"\d+\.\s+(\w+)"
    matches = re.findall(pattern, text_response)
    moods = list(matches)
    print(moods)


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


def random_transition(clip, duration):
    transitions = [crossfadein, crossfadeout, slide_in, slide_out]
    transition = random.choice(transitions)

    if transition in [slide_in, slide_out]:
        sides = ['top', 'bottom', 'left', 'right']
        side = random.choice(sides)
        return transition(clip, duration, side)
    else:
        return transition(clip, duration)


def get_media_files(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_FILE_TYPE)]
    video_files = [f for f in os.listdir(folder) if f.lower().endswith(('mp4', 'mov', 'avi'))]
    print("Media files collected")
    return image_files, video_files


def create_video(media_folder, output_path, fps=24):
    script = get_script()

    add_voice(script)
    speed_up_audio("script.mp3", 1.01)

    audio_clip = AudioFileClip('script_sped_up.mp3')
    audio_duration = audio_clip.duration

    image_files, video_files = get_media_files(media_folder)

    if not image_files and not video_files:
        raise ValueError("No media files to create video")

    if video_files:
        for video_file in video_files:
            video_clip = VideoFileClip(os.path.join(media_folder, video_file))
            if video_clip.duration > 60:
                video_clip = video_clip.subclip(0, audio_duration)
                if video_clip.size[0] / video_clip.size[1] != WIDTH / HEIGHT:
                    video_clip = crop_video_to_aspect_ratio(video_clip, WIDTH, HEIGHT)
                final_clip = video_clip.set_audio(audio_clip)
                final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac')
                add_subtitles(output_path)
                break
        else:
            cropped_images = []
            for image_file in tqdm(image_files, desc="Cropping images", unit="image"):
                img_clip = crop_image(image_file)
                if img_clip is not None:
                    img_clip = img_clip.set_duration(audio_duration / len(image_files)).set_position(
                        ("center", "center"))
                    img_clip = random_transition(img_clip, audio_duration / len(image_files))
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
        os.remove("output_video.mp4")

    if os.path.exists(SUBTITLE_FILE_PATH):
        os.remove(SUBTITLE_FILE_PATH)


create_video(IMAGE_FOLDER_PATH, 'output_video.mp4', fps=30)
