
import os
import sys
import pygame


def resource_path(relative_path):
    """Lấy đường dẫn tài nguyên, hỗ trợ cả PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


class SoundManager:
    def __init__(self):
        # Khởi tạo pygame mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error as e:
            print(f"Lỗi khởi tạo âm thanh: {e}")
            self.correct_sound = None
            self.wrong_sound = None
            self.click_sound = None
            return

        # Tải âm thanh
        self.correct_sound = self._load_sound(
            ("right_answer_sound_effect", "correct"),
            "âm thanh trả lời đúng"
        )

        self.wrong_sound = self._load_sound(
            ("Am_thanh_that_vong", "wrong"),
            "âm thanh trả lời sai"
        )

        # Âm thanh click là tùy chọn
        self.click_sound = self._load_sound(
            ("click",),
            "âm thanh click",
            required=False
        )

    def _load_sound(self, prefixes, description, required=True):
        """Tìm và tải file âm thanh từ thư mục sounds."""
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Hỗ trợ cả khi file Python nằm trong assets
        # hoặc nằm ở thư mục gốc của dự án.
        base_dirs = [
            current_dir,
            os.path.dirname(current_dir),
        ]

        if hasattr(sys, "_MEIPASS"):
            base_dirs.insert(0, sys._MEIPASS)

        sound_dirs = []
        for base_dir in base_dirs:
            sound_dirs.append(
                os.path.join(base_dir, "assets", "sounds")
            )
            sound_dirs.append(
                os.path.join(base_dir, "sounds")
            )

        for sound_dir in sound_dirs:
            if not os.path.isdir(sound_dir):
                continue

            for filename in os.listdir(sound_dir):
                name_lower = filename.lower()

                if (
                    name_lower.startswith(
                        tuple(prefix.lower() for prefix in prefixes)
                    )
                    and name_lower.endswith((".mp3", ".wav", ".ogg"))
                ):
                    sound_path = os.path.join(sound_dir, filename)

                    try:
                        return pygame.mixer.Sound(sound_path)
                    except (pygame.error, OSError) as e:
                        print(f"Lỗi tải {description}: {e}")
                        return None

        if required:
            print(f"CẢNH BÁO: Không tìm thấy {description}.")

        return None

    def _play_sound(self, sound):
        """Phát âm thanh không chặn giao diện game."""
        if sound is not None:
            sound.play()

    def play_correct(self):
        """right_answer_sound_effect-www_tiengdong_com.mp3"""
        self._play_sound(self.correct_sound)

    def play_wrong(self):
        """Am_thanh_that_vong-www_tiengdong_com.mp3"""
        self._play_sound(self.wrong_sound)

    def play_click(self):
        """tieng_danh_ram_meme-www_tiengdong_com.mp3"""
        self._play_sound(self.click_sound)
