"""Brain Quest - SQLite + Open Trivia Database API + pygame sound effects.

Expected files when running from source:
    brainquest.py
    sound_manager.py
    brain_quest.db
    sounds/
        Am_thanh_that_vong-....mp3
        right_answer_sound_effect-....mp3

The SoundManager searches both ``sounds/`` and ``assets/sounds/`` locations.
"""

import html
import os
import random
import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import requests

from sound_manager import SoundManager


OPENTDB_API_URL = "https://opentdb.com/api.php"


def resource_path(relative_path: str) -> str:
    """Return a path to a bundled resource or a file beside this script."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# Keep the database beside this script when running normally. When packaged,
# keep it beside the executable so database changes can persist between runs.
if getattr(sys, "frozen", False):
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "brain_quest.db")
else:
    DB_PATH = resource_path("brain_quest.db")


class QuizAppWithSound(tk.Tk):
    """Main Tkinter quiz application."""

    def __init__(self):
        super().__init__()

        self.title("SNLT-HP8-B3-ProjectBasic (Âm thanh)")
        self.geometry("650x500")
        self.resizable(False, False)

        self.current_question_data = None
        self.current_score = 0
        self.current_question_is_from_api = False

        # SoundManager handles pygame initialization and loading sound files.
        self.sound_manager = SoundManager()

        self._setup_ui()
        self._load_and_display_question_from_db()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------
    def _connect_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            return conn, conn.cursor()
        except sqlite3.Error as exc:
            messagebox.showerror(
                "Lỗi CSDL",
                f"Không thể kết nối đến CSDL:\n{exc}",
                parent=self,
            )
            return None, None

    def _load_question_from_db(self):
        """Load a random question from SQLite; options are semicolon-separated."""
        conn, cursor = self._connect_db()
        if conn is None:
            return None

        try:
            cursor.execute(
                """
                SELECT question_text, options_text, correct_answer_text
                FROM questions
                ORDER BY RANDOM()
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row is None:
                return None

            question_text, options_text, correct_answer = row
            options = [option.strip() for option in options_text.split(";") if option.strip()]
            return {
                "question": question_text,
                "options": options,
                "correct_answer_text": correct_answer,
            }
        except sqlite3.Error as exc:
            messagebox.showerror(
                "Lỗi truy vấn CSDL",
                "Không thể tải câu hỏi. Hãy kiểm tra bảng questions có các cột "
                "question_text, options_text và correct_answer_text.\n\n"
                f"Chi tiết: {exc}",
                parent=self,
            )
            return None
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # API helper
    # ------------------------------------------------------------------
    def _fetch_question_from_api(self):
        """Fetch one multiple-choice question from Open Trivia Database."""
        params = {
            "amount": 1,
            "category": 15,
            "type": "multiple",
        }

        try:
            response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("response_code") != 0 or not data.get("results"):
                messagebox.showerror(
                    "Lỗi API",
                    "API không trả về câu hỏi hợp lệ. "
                    f"Mã phản hồi: {data.get('response_code')}",
                    parent=self,
                )
                return None

            item = data["results"][0]
            question_text = html.unescape(item.get("question", ""))
            correct_answer = html.unescape(item.get("correct_answer", ""))
            incorrect_answers = [
                html.unescape(answer)
                for answer in item.get("incorrect_answers", [])
            ]
            options = incorrect_answers + [correct_answer]
            random.shuffle(options)

            return {
                "question": question_text,
                "options": options,
                "correct_answer_text": correct_answer,
            }

        except requests.exceptions.Timeout:
            messagebox.showerror(
                "Lỗi kết nối",
                "Hết thời gian chờ khi kết nối API.",
                parent=self,
            )
        except requests.exceptions.RequestException as exc:
            messagebox.showerror(
                "Lỗi kết nối",
                f"Không thể lấy câu hỏi từ Internet:\n{exc}",
                parent=self,
            )
        except (ValueError, KeyError, TypeError) as exc:
            messagebox.showerror(
                "Lỗi dữ liệu API",
                f"Dữ liệu API không hợp lệ:\n{exc}",
                parent=self,
            )
        return None

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        source_frame = ttk.Frame(main_frame)
        source_frame.pack(pady=(0, 15), fill=tk.X)

        ttk.Label(source_frame, text="Nguồn câu hỏi:").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(
            source_frame,
            text="Từ CSDL Local",
            command=self._on_db_source_clicked,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            source_frame,
            text="Từ Internet (API)",
            command=self._on_api_source_clicked,
        ).pack(side=tk.LEFT, padx=5)

        self.question_label = ttk.Label(
            main_frame,
            text="Đang tải câu hỏi...",
            font=("Arial", 16, "bold"),
            wraplength=600,
            justify="center",
        )
        self.question_label.pack(pady=20)

        self.options_frame = ttk.Frame(main_frame)
        self.options_frame.pack(pady=10)
        self.option_buttons = []

        style = ttk.Style(self)
        style.configure("Option.TButton", font=("Arial", 11), padding=5)

        for index in range(4):
            button = ttk.Button(
                self.options_frame,
                text="",
                command=lambda idx=index: self._option_selected(idx),
                width=30,
                style="Option.TButton",
                state=tk.DISABLED,
            )
            button.grid(
                row=index // 2,
                column=index % 2,
                padx=10,
                pady=5,
                sticky="ew",
            )
            self.option_buttons.append(button)

        self.score_label = ttk.Label(
            main_frame,
            text=f"Điểm: {self.current_score}",
            font=("Arial", 13),
        )
        self.score_label.pack(pady=10)

        self.result_feedback_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 12, "italic"),
        )
        self.result_feedback_label.pack(pady=5)

        self.next_button = ttk.Button(
            main_frame,
            text="Câu Tiếp Theo",
            command=self._handle_next_question_logic,
            state=tk.DISABLED,
        )
        self.next_button.pack(pady=15)

    # ------------------------------------------------------------------
    # Event handlers for source buttons
    # ------------------------------------------------------------------
    def _on_db_source_clicked(self):
        self.sound_manager.play_click()
        self._load_and_display_question_from_db()

    def _on_api_source_clicked(self):
        self.sound_manager.play_click()
        self._load_and_display_question_from_api()

    def _load_and_display_question_from_db(self):
        self.current_question_is_from_api = False
        self.current_question_data = self._load_question_from_db()
        self._update_ui_with_current_question()

    def _load_and_display_question_from_api(self):
        self.question_label.config(text="Đang tải câu hỏi từ Internet...")
        self.update_idletasks()

        # Disable old answers while the API request is in progress.
        for button in self.option_buttons:
            button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)

        question_data = self._fetch_question_from_api()
        if question_data:
            self.current_question_is_from_api = True
            self.current_question_data = question_data
            self._update_ui_with_current_question()
        else:
            self.current_question_data = None
            self.question_label.config(
                text="Không tải được câu hỏi. Hãy thử lại hoặc chọn CSDL Local."
            )
            self.result_feedback_label.config(text="")
            for button in self.option_buttons:
                button.config(text="", state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

    def _update_ui_with_current_question(self):
        if not self.current_question_data:
            self.question_label.config(
                text="Không có câu hỏi trong CSDL. Hãy thêm dữ liệu hoặc chọn API."
            )
            for button in self.option_buttons:
                button.config(text="", state=tk.DISABLED)
            self.result_feedback_label.config(text="")
            self.next_button.config(state=tk.DISABLED)
            return

        question_data = self.current_question_data
        self.question_label.config(text=question_data["question"])
        self.result_feedback_label.config(text="")
        self.next_button.config(state=tk.DISABLED)

        options = question_data["options"]
        for index, button in enumerate(self.option_buttons):
            if index < len(options):
                button.config(text=options[index], state=tk.NORMAL)
            else:
                button.config(text="", state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Answer checking and next question
    # ------------------------------------------------------------------
    def _option_selected(self, index):
        if not self.current_question_data:
            return

        options = self.current_question_data["options"]
        if not (0 <= index < len(options)):
            return

        selected_answer = options[index]
        correct_answer = self.current_question_data["correct_answer_text"]

        # Disable all answers so the score and sound trigger only once.
        for button in self.option_buttons:
            button.config(state=tk.DISABLED)

        if selected_answer == correct_answer:
            self.current_score += 10
            self.result_feedback_label.config(
                text="Chính xác!",
                foreground="green",
            )
            self.sound_manager.play_correct()
        else:
            self.result_feedback_label.config(
                text=f"Sai rồi! Đáp án đúng là: {correct_answer}",
                foreground="red",
            )
            self.sound_manager.play_wrong()

        # Always update score and enable the next-question button.
        self.score_label.config(text=f"Điểm: {self.current_score}")
        self.next_button.config(state=tk.NORMAL)

    def _handle_next_question_logic(self):
        self.sound_manager.play_click()
        if self.current_question_is_from_api:
            self._load_and_display_question_from_api()
        else:
            self._load_and_display_question_from_db()

    def _on_close(self):
        try:
            self.sound_manager.close()
        except Exception:
            # Older SoundManager versions may not define close().
            pass
        self.destroy()


def initialize_database():
    """Create the expected questions table if the database is new."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options_text TEXT NOT NULL,
                    correct_answer_text TEXT NOT NULL
                )
                """
            )
    except sqlite3.Error as exc:
        print(f"Lỗi khởi tạo CSDL: {exc}")


if __name__ == "__main__":
    initialize_database()
    app = QuizAppWithSound()
    app.mainloop()
