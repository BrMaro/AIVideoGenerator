from moviepy.editor import *
from moviepy.video.fx.resize import resize
from moviepy.video.fx.all import *
import random
import os
from tqdm import tqdm
import numpy as np
from PIL import Image
from gtts import gTTS

IMAGE_FOLDER_PATH = "C:\\Users\\Techron\\PycharmProjects\\AI Video Generator\\Images"
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



def get_image_files(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith(FILE_TYPE)]
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
    resized_images = [resize_image(f) for f in image_files]

    add_sound(get_script())
    audio_clip = AudioFileClip('script.mp3')
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
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', audio=True)

create_video(IMAGE_FOLDER_PATH, 'output_video.mp4', fps=30)