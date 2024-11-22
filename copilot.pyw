import io
import os
import base64
import json
import sys, time
from pathlib import Path
import sounddevice as sd
from contextlib import suppress

import numpy as np
import requests
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit,QCheckBox
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QBuffer, QByteArray, QIODevice, QSettings
from PySide6.QtGui import QIcon, QMouseEvent, QFont, QColor, QClipboard, QPixmap, QScreen
import soundfile as sf
# import anthropic
import utils
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

workspace_dir = Path(__file__).parent / "workspace"
workspace_dir.mkdir(exist_ok=True)

required_vars = ['SAMBANOVA_API_KEY', 'GROQ_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"Missing required environment variables: {', '.join(missing_vars)}")
    print(f"Please set them in .env")

colors = {
    "btnbg": "#ed7424",
    "success": "#fff",
}
STYLESHEET = f"""
    QWidget#mainWidget {{
        background-color: #182640;
        border-radius: 10px;
        border: 1px solid #333;
    }}
    QPushButton {{
        background-color: {colors['btnbg']};
        color: white;
        border: none;
        padding: 5px;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        border-radius: 0.25em;
    }}
    QPushButton:hover {{
        background-color: {colors['success']};
    }}
    QPushButton:pressed {{
        background-color: yellow;
    }}
    QLabel{{
        color: #ffffff;
    }}
    QPushButton#closeButton {{
        background-color: transparent;
        color: #cccccc; 
        font-size: 20px;
        border-radius: 5px;
        padding: 2px;
        margin: 0px;
    }}
    QPushButton#closeButton:hover {{
        background-color: #ff2222;
}}
    QCheckBox {{
        color: white;
        spacing: 5px;
        padding: 4px 8px;
        border-radius: 0.25em;
        background-color: rgba(0, 0, 0, 0.5);
    }}

    QCheckBox:hover {{
        background-color: #3d3d3d;
    }}

    QCheckBox:checked {{
        background-color: {colors['btnbg']};
    }}

    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 7px;
        border: 1px solid #999;
        background: transparent;
    }}

    QCheckBox::indicator:checked {{
        background-color: white;
        border: 1px solid white;
    }}
"""

def generate_sine_wave(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    return wave.astype(np.float32)


class ModernWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.dp, self.r, self.ad, self.sr, self.st = QPoint(), 0, [], 44100, None
        self.screen_capture = None
        self.transcription = ""
        self.initUI()
        self.initShortcuts()

    def initShortcuts(self):
        self.rec_btn.setShortcut("1")
        self.capture_button.setShortcut("2")
        self.send_button.setShortcut("3")
        self.type_button.setShortcut("4")
    def _exit(self):
        import soundfile as sf
        
        try:
            # Read the mp3 file
            data, samplerate = sf.read("exit.mp3")
            
            # Play using sounddevice
            sd.play(data, samplerate)
            # Wait until file is done playing
            sd.wait()
            
        except Exception as e:
            print(f"Error playing exit sound: {e}")
        finally:
            # Close application
            QApplication.quit()
            
    def initUI(self):
        self.setStyleSheet(STYLESHEET)

        main_widget = QWidget(self)
        main_widget.setObjectName("mainWidget")

        # Main container layout
        container_layout = QVBoxLayout(main_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Top bar with close button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(5, 0, 0, 5)

        title_label = QLabel("SambaNova Copilot")
        title_label.setStyleSheet("font-size: 16px; color: #fff; background: #000; padding: 0 4px; border-radius: 4px; ")

        close_button = QPushButton("☢️")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self._exit)

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(close_button)

        # Main content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)

        # Layout 1: Button Area
        button_area = QHBoxLayout()
        button_area.setSpacing(5)

        # Configure buttons with emoji labels
        SIZE = QSize(32, 32)

        # Create buttons
        self.rec_btn = QPushButton("🎤")
        self.type_button = QPushButton("⌨️")
        self.capture_button = QPushButton("📸")
        self.send_button = QPushButton("🤖")

        # Configure all buttons
        buttons_config = [
            (self.rec_btn, self.tr, "Record Audio (🎤 Voice Capture)"),
            (self.capture_button, self.capture_screen, "Capture Screen (📸 Screenshot)"),
            (self.send_button, self.send_to_claude, "Send to AI (🧠 Process)"),
            (self.type_button, self.type_copied_text, "Quick Type (⌨️ Auto-type)"),
        ]

        # Add buttons vertically to button area
        for btn, callback, tooltip in buttons_config:
            # btn.setIconSize(SIZE)
            btn.setFixedSize(48, 48)
            btn.clicked.connect(callback)
            btn.setToolTip(tooltip)
            button_area.addWidget(btn)

        button_area.addStretch()
        # Add checkboxes
        checkbox_layout = QHBoxLayout()
        self.clipboard_checkbox = QCheckBox("clipboard")
        self.workspace_checkbox = QCheckBox("workspace") 
        self.agent_checkbox = QCheckBox("agent mode")

        # Configure each checkbox
        for checkbox in [self.clipboard_checkbox, self.workspace_checkbox, self.agent_checkbox]:
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox_layout.addWidget(checkbox)
        
        checkbox_layout.addStretch()

        # Add checkbox layout below buttons
        content_layout.addLayout(button_area)
        content_layout.addLayout(checkbox_layout)
        # Layout 2: Screen Area
        screen_area = QVBoxLayout()
        screen_area.setSpacing(5)

        self.screen_view = QLabel()
        self.screen_view.setFixedSize(320, 180)  # 16:9 aspect ratio
        self.screen_view.setStyleSheet(
            """

            border-radius: 5px;
            background-color: rgba(0, 0, 0, 0.5);
            """
        )
        screen_area.addWidget(self.screen_view)

        self.status_label = QLabel("🟢Ready to record")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setStyleSheet("color: #999; margin-top: 10px;")
        self.status_label.setWordWrap(True)
        screen_area.addWidget(self.status_label)
        screen_area.addStretch()

        # Add layouts to content area
        content_layout.addLayout(button_area)
        content_layout.addLayout(screen_area)

        # Add all layouts to container
        container_layout.addLayout(top_bar)
        container_layout.addLayout(content_layout)

        self.setWindowTitle('Swamix Copilot')
        self.show()

    def sizeHint(self):
        return QSize(600, 400)

    def type_copied_text(self, warns=3):
        import pyautogui

        beep_frequency = 15000  # Frequency in Hz
        beep_duration = 0.3  # Duration in seconds
        beep_wave = generate_sine_wave(beep_frequency, beep_duration)

        sd.play(beep_wave, samplerate=44100, blocking=True)

        time.sleep(3)
        # print(QApplication.clipboard().text())
        pyautogui.typewrite(list(QApplication.clipboard().text()), 0.01)

    def tr(self):
        if not self.r:
            self.r = 1
            # self.rec_btn.setText("Stop Recording")
            self.rec_btn.setStyleSheet(f"background-color: {colors['success']}")
            self.status_label.setText("Recording...")
            self.ad = []
            self.st = sd.InputStream(callback=self.ac, channels=1, samplerate=self.sr)
            self.st.start()
        else:
            self.r = 0
            # self.rec_btn.setText("Record Audio")
            self.rec_btn.setStyleSheet(STYLESHEET)
            self.status_label.setText("Processing...")
            self.st and (self.st.stop(), self.st.close())
            self.pa()

    def ac(self, i, f, t, st):
        st and print(st)
        self.r and self.ad.append(i.copy())

    def pa(self):
        if not self.ad:
            self.status_label.setText("No audio data recorded")
            return
        audio_data = np.concatenate(self.ad, axis=0)
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, self.sr, format='wav')
        audio_buffer.seek(0)
        self.transcribe_audio(audio_buffer)

    def transcribe_audio(self, af):
        self.status_label.setText("Transcribing...")
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            files={"file": ("audio.wav", af, "audio/wav")},
            data={"model": "whisper-large-v3-turbo", "temperature": 0, "response_format": "json", "language": "en"},
        )
        result = r.json()['text'] if r.status_code == 200 else f"Error:{r.status_code} {r.text}"
        self.transcription = result
        self.status_label.setText(f"Transcription: {result}")
        # print("Transcription:", result)
        if not self.clipboard_checkbox.isChecked():
            QApplication.clipboard().setText(result)
            self.status_label.setText(f"Clippied: {result}")

    def capture_screen(self):
        screen = QApplication.primaryScreen()
        self.screen_capture = screen.grabWindow(0)
        scaled_pixmap = self.screen_capture.scaled(self.screen_view.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.screen_view.setPixmap(scaled_pixmap)
        self.status_label.setText("Screen captured")
        
    def send_to_claude(self):
        try:
            # Validate inputs
            if not self.screen_capture and not self.transcription:
                self.status_label.setText("Error: Please provide either an image or voiceover")
                return

            self.status_label.setText("Sending to OpenAI...")

            # Convert QPixmap to base64-encoded string if screen capture exists
            image_base64 = None
            if self.screen_capture:
                try:
                    buffer = QByteArray()
                    buffer_io = QBuffer(buffer)
                    buffer_io.open(QIODevice.OpenModeFlag.WriteOnly)
                    with suppress(Exception):
                        self.screen_capture.save(buffer_io, "PNG")
                    image_base64 = buffer.toBase64().toStdString()
                except Exception as e:
                    self.status_label.setText(f"Error processing image: {str(e)}")
                    return
                finally:
                    buffer_io.close()

            # Validate API key
            api_key = os.getenv('SAMBANOVA_API_KEY')
            if not api_key:
                self.status_label.setText("Error: APIKEY not found in environment variables")
                return

            # Create OpenAI client
            client = OpenAI(base_url="https://api.sambanova.ai/v1", api_key=api_key)

            # use clipboard if selected
            clippy = ""
            if self.clipboard_checkbox.isChecked():
                clippy = QApplication.clipboard().text()
                print(f"Clipboard: {clippy[:1000]}")
            
            # Build message content
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an interview assistant copilot. first reason out with what you will do, make a good hypothesis, and then seperate it and give final answer
                    
                    # Example:
                    ...reasoning...
                    -----
                    ...answer...
                    
                    # Contexts
                    <Clipboard>
                    {clippy}
                    </Clipboard>
                    """.replace("\n\n", "\n").replace("\t", " ")
                }
            ]

            if self.transcription:
                messages.append({
                    "role": "user", 
                    "content": f"Transcript: {self.transcription}"
                })
            # Add image message if image exists
            if image_base64:
                messages[0]['role']="user"
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "text": "Analyze this image carefully and " +  self.transcription,
                            "type": "text"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                })

            # Add transcript if exists

            # Send request to OpenAI
            try:
                response = client.chat.completions.create(
                    model="Llama-3.2-11B-Vision-Instruct" if image_base64 else "Meta-Llama-3.1-405B-Instruct",
                    messages=messages,
                    max_tokens=2048,
                )
                # print(response)
                ai_response = response.choices[0].message.content
                self.show_claude_response(ai_response)

                # Copy response to clipboard
                clipboard = QApplication.clipboard()
                clipboard.setText(ai_response)
                self.status_label.setText("Response received and copied to clipboard")

            except Exception as e:
                self.status_label.setText(f"API Error: {str(e)}")

        except Exception as e:
            self.status_label.setText(f"Critical error: {str(e)}")

    def show_claude_response(self, response):
        dialog = QDialog(self)
        dialog.setWindowTitle("Claude's Response")
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(response)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(response))
        layout.addWidget(copy_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.resize(500, 400)
        dialog.exec()

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        self.status_label.setText("Response copied to clipboard")

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.dp = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.dp)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent):
        self.dp = QPoint()
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setDesktopSettingsAware(False)
    window = ModernWidget()
    # window.setWindowOpacity(0.9)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    # app = QApplication()
    # app.setDesktopSettingsAware(False)

    # window = ModernWidget()
    # window.setWindowOpacity(0.8)

    # sys.exit(app.exec())
