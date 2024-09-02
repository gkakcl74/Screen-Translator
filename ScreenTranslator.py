import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageGrab, Image
import pytesseract
from googletrans import Translator
import pyautogui

# Tesseract 경로 설정 (Windows의 경우)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 번역기 초기화
translator = Translator()

class ScreenTranslatorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("실시간 스크린 번역기")
        self.master.geometry("400x500")
        self.is_translating = False
        self.capture_region = None
        self.translate_thread = None

        # UI 구성
        self.create_widgets()

    def create_widgets(self):
        # 영역 선택 버튼
        self.select_region_button = ttk.Button(self.master, text="번역할 영역 선택", command=self.select_region)
        self.select_region_button.pack(pady=10)

        # 대상 언어 선택 콤보박스
        self.language_label = ttk.Label(self.master, text="어떤 언어로 번역:")
        self.language_label.pack()
        self.language_var = tk.StringVar()
        self.language_combobox = ttk.Combobox(self.master, textvariable=self.language_var, state="readonly")
        self.language_combobox['values'] = sorted(['ko', 'en', 'ja', 'zh-cn', 'zh-tw', 'de', 'fr', 'es', 'ru', 'it', 'pt'])
        self.language_combobox.current(0)
        self.language_combobox.pack(pady=5)

        # 갱신 간격 설정
        self.interval_label = ttk.Label(self.master, text="갱신 간격 (초):")
        self.interval_label.pack()
        self.interval_var = tk.DoubleVar(value=1.0)
        self.interval_spinbox = ttk.Spinbox(self.master, from_=0.5, to=10.0, increment=0.5, textvariable=self.interval_var, width=5)
        self.interval_spinbox.pack(pady=5)

        # 번역 시작/중지 버튼
        self.start_button = ttk.Button(self.master, text="번역 시작", command=self.start_translation)
        self.start_button.pack(pady=10)

        self.stop_button = ttk.Button(self.master, text="번역 중지", command=self.stop_translation, state="disabled")
        self.stop_button.pack(pady=5)

        # 번역 결과 표시 텍스트 박스
        self.result_text = tk.Text(self.master, wrap="word", height=20)
        self.result_text.pack(padx=10, pady=10, fill="both", expand=True)

    def select_region(self):
        messagebox.showinfo("영역 선택", "마우스를 드래그하여 번역할 영역을 선택하세요.")
        self.master.withdraw()
        time.sleep(0.5)  # 창이 완전히 사라질 때까지 대기

        # 화면 전체 스크린샷 촬영
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.convert("RGBA")

        # 영역 선택을 위한 임시 창 생성
        selection_window = tk.Toplevel()
        selection_window.attributes("-alpha", 0.3)
        selection_window.attributes("-topmost", True)
        selection_window.overrideredirect(True)

        fullscreen_width, fullscreen_height = screenshot.size
        selection_window.geometry(f"{fullscreen_width}x{fullscreen_height}+0+0")

        canvas = tk.Canvas(selection_window, width=fullscreen_width, height=fullscreen_height)
        canvas.pack()

        rect = None
        start_x = start_y = 0

        def on_mouse_down(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)

        def on_mouse_move(event):
            nonlocal rect
            if rect:
                canvas.coords(rect, start_x, start_y, event.x, event.y)

        def on_mouse_up(event):
            nonlocal rect
            end_x, end_y = event.x, event.y
            self.capture_region = (min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))
            canvas.destroy()
            selection_window.destroy()
            self.master.deiconify()
            messagebox.showinfo("영역 선택 완료", f"선택된 영역: {self.capture_region}")

        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

        selection_window.mainloop()

    def start_translation(self):
        if self.capture_region is None:
            messagebox.showwarning("영역 선택 필요", "번역할 영역을 먼저 선택하세요.")
            return

        if not self.is_translating:
            self.is_translating = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.translate_thread = threading.Thread(target=self.translate_loop, daemon=True)
            self.translate_thread.start()

    def stop_translation(self):
        if self.is_translating:
            self.is_translating = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def translate_loop(self):
        while self.is_translating:
            screenshot = ImageGrab.grab(bbox=self.capture_region)
            text = pytesseract.image_to_string(screenshot)

            if text.strip():
                try:
                    translated = translator.translate(text, dest=self.language_var.get())
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, translated.text)
                except Exception as e:
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, f"번역 오류: {e}")
            else:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "텍스트를 인식하지 못했습니다.")

            time.sleep(self.interval_var.get())

def main():
    root = tk.Tk()
    app = ScreenTranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
