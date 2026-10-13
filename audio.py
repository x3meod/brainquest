import os
import pygame

# Thư mục chứa file âm thanh
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")

pygame.mixer.init()


def load_sound(filename_prefix):
    for filename in os.listdir(SOUNDS_DIR):
        if (
            filename.lower().startswith(filename_prefix.lower())
            and filename.lower().endswith((".mp3", ".wav", ".ogg"))
        ):
            path = os.path.join(SOUNDS_DIR, filename)
            return pygame.mixer.Sound(path)

    raise FileNotFoundError(
        f"Không tìm thấy âm thanh: {filename_prefix}"
    )


# Âm thanh khi trả lời sai
wrong_sound = load_sound("Am_thanh_that_vong")

# Âm thanh khi trả lời đúng
correct_sound = load_sound("right_answer_sound_effect")


def play_wrong_sound():
    wrong_sound.play()


def play_correct_sound():
    correct_sound.play()