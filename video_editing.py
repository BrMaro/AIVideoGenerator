from moviepy.editor import *
from moviepy.video.fx.resize import resize
from moviepy.video.fx.all import *
import random
import os
from tqdm import tqdm
import numpy as np
from PIL import Image
from gtts import gTTS
import re
from moviepy.config import change_settings


change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

PROJECT_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator"
IMAGE_FOLDER_PATH = os.path.join(PROJECT_PATH,"Images")
SUBTITLE_FILE_PATH = os.path.join(PROJECT_PATH,"subtitles.txt")

FILE_TYPE = ".jpg"
HEIGHT = 1080
ASPECT_RATIO = 9/16
WIDTH = round(HEIGHT*ASPECT_RATIO)
DURATION_PER_IMAGE = 2
language = 'en'

def get_script():
    with open('script.txt','r') as file:
        content = file.read()
        return content


def generate_subtitles_file(script,max_characters_per_line=20):
    words = re.findall(r'\b\w+\b', script)
    subtitle_lines = []

    current_line = []
    current_line_length = 0

    for word in words:
        if current_line_length + len(word) > max_characters_per_line:
            subtitle_lines.append(' '.join(current_line))
            current_line = [word]
            current_line_length = len(word)
        else:
            current_line.append(word)
            current_line_length += len(word)

    # Add the last line
    subtitle_lines.append(' '.join(current_line))

    # Generate the subtitle file content
    subtitle_content = '\n'.join(f'{i*2:.2f} {(i+1)*2:.2f} {line}' for i, line in enumerate(subtitle_lines))

    with open(os.path.join(PROJECT_PATH,"subtitles.txt"),'w') as file:
        file.write(subtitle_content)


def load_subtitles(subtitle_file):
    subtitles = []
    with open(subtitle_file,"r") as file:
        for line in file:
            start = line.strip().split(' ')[0]
            end = line.strip().split(' ')[1]
            caption = " ".join(line.strip().split(' ')[2:])
            subtitles.append((float(start), float(end), caption))

    return subtitles


def create_text_clips(subtitle_file):

    subtitles = load_subtitles(subtitle_file)
    text_clips = []
    for start,end,caption in subtitles:
        text_clip = TextClip(caption, fontsize=24, color='white',bg_color='black',size=(1920, 1080), method='caption', align='center')
        text_clip = text_clip.set_start(start).set_duration(end-start)
        text_clips.append(text_clip)

    print("Subtitle clips created")
    return text_clips


def get_image_files(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith(FILE_TYPE)]
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
    mysound = gTTS(text=script,lang=language)
    mysound.save("script.mp3")


def create_video(image_folder, output_path, fps=24):
    image_files = get_image_files(image_folder)

    resized_images = []
    for image_file in tqdm(image_files, desc="Resizing images", unit="image"):
        resized_image = resize_image(image_file)
        resized_images.append(resized_image)


    text_clips = create_text_clips(SUBTITLE_FILE_PATH)

    add_sound(get_script())
    audio_clip = AudioFileClip('script.mp3')
    sound_file_duration = audio_clip.duration


    clips = []
    transitions = [
        lambda c: c.fx(vfx.fadeout, 0.3).fx(vfx.fadein, 0.3),
        lambda c: c.fx(all.crossfadein, duration=0.5).fx(all.crossfadeout, duration=0.5),
        lambda c: c.fx(all.spin_in),
    ]

    for i in tqdm(range(len(image_files)), desc="Creating Video", unit="clip"):
        img_clip = resized_images[i].set_duration(DURATION_PER_IMAGE).set_position(("center", "center"))

        # random_transition = random.choice(transitions)
        # img_clip = random_transition(img_clip)
        # # Adding transitions
        img_clip = img_clip.fx(vfx.fadeout,0.2).fx(vfx.fadein,0.2)
        clips.append(img_clip)

    final_clip = concatenate_videoclips(clips,method='compose')

    # final_clip = CompositeVideoClip([final_clip,*text_clips])
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', audio=True)

create_video(IMAGE_FOLDER_PATH, 'output_video.mp4', fps=30)