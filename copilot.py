import io, os, base64, json, sys, time, math, logging
import sounddevice as sd
import requests

from pathlib import Path
from contextlib import suppress
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit, QCheckBox
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QBuffer, QByteArray, QIODevice, QSettings
from PySide6.QtGui import QIcon, QMouseEvent, QFont, QColor, QClipboard, QPixmap, QScreen

import utils
import vdb

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('copilot.log'), logging.StreamHandler()]
)

# WORKSPACE_DIR
(Path(__file__).parent / os.getenv('WORKSPACE_DIR', '.workspace')).mkdir(exist_ok=True)
# ARTIFACT_DIR
(Path(__file__).parent / os.getenv('ARTIFACT_DIR', '.artifacts')).mkdir(exist_ok=True)

required_vars = ['SAMBANOVA_API_KEY', 'GROQ_API_KEY', "VOYAGE_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)} Please set them in .env, an editor will open for convenience")
    r = os.system("code ./.env")
    if r == 1:
        logging.error("Could not open .env file with VSCODE shortcut, using notepapdi")
        r = os.system("notepad ./.env")
    print(r)
    # os.system("explorer ./.env")

# VECTOR STORE
my_vdb = vdb.VectorDB()
logging.info(f"VectorDB initialized has {my_vdb.client.count(my_vdb.default_collection)} docs")
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
    # Calculate number of samples
    num_samples = int(sample_rate * duration)
    # Generate samples using pure Python
    wave = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.5 * math.sin(2 * math.pi * frequency * t)
        wave.append(float(sample))
    return wave


class ModernWidget(QWidget):
    def __init__(self):
        super().__init__()
        logging.info("Initializing Copilot")

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.dp, self.r, self.ad, self.sr, self.st = QPoint(), 0, [], 44100, None
        self.screen_capture = None
        self.transcription = ""
        self.initUI()
        self.initShortcuts()
        logging.info("Initializing Success")

    def initShortcuts(self):
        self.rec_btn.setShortcut("1")
        self.capture_button.setShortcut("2")
        self.send_button.setShortcut("3")
        self.type_button.setShortcut("4")

    def _exit(self):
        import soundfile as sf

        try:
            data, samplerate = sf.read(utils.get_resource_path("assets/exit.mp3"))
            sd.play(data, samplerate)
            sd.wait()

        except Exception as e:
            print(f"Error playing exit sound: {e}")
        finally:
            # Close application
            QApplication.quit()

    def initUI(self):
        self.setStyleSheet(STYLESHEET)
        # with open('ashiled.txt', 'w') as f:
        #     f.write(str(os.listdir(utils.get_resource_path('assets'))))
        #     f.write(utils.get_first_google_result('recepie for biscuit'))

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
        self.reset_button = QPushButton("🔄")

        # Configure all buttons
        buttons_config = [
            (self.rec_btn, self.tr, "Record Audio (🎤 Voice Capture)"),
            (self.capture_button, self.capture_screen, "Capture Screen (📸 Screenshot)"),
            (self.send_button, self.send_to_ai, "Send to AI (🧠 Process)"),
            (self.type_button, self.type_copied_text, "Quick Type (⌨️ Auto-type)"),
            (self.reset_button, self.reset_data, "Reset Data (🔄 Clear)"),
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
        self.clipboard_checkbox = QCheckBox("Clipboard")
        self.workspace_checkbox = QCheckBox("Workspace")
        self.websearch_checkbox = QCheckBox("Web Search")

        # Configure each checkbox
        for checkbox in [self.clipboard_checkbox, self.workspace_checkbox, self.websearch_checkbox]:
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox_layout.addWidget(checkbox)

        checkbox_layout.addStretch()

        # Add transcript text edit
        self.transcript_edit = QTextEdit()
        self.transcript_edit.setPlaceholderText("Narration will appear here...")
        self.transcript_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
        """
        )

        self.transcript_edit.textChanged.connect(self.on_transcript_changed)
        self.transcript_edit.setFixedHeight(40)
        # Add checkbox layout below buttons
        content_layout.addLayout(button_area)
        content_layout.addLayout(checkbox_layout)
        content_layout.addWidget(self.transcript_edit)

        # ---------- Layout 2: Screen Area
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

    def reset_data(self):
        self.screen_capture = None
        self.transcription = ""
        self.screen_view.clear()
        self.status_label.setText("🟢 Data cleared")
        QApplication.clipboard().clear()

    def type_copied_text(self, warns=3):
        import pyautogui

        beep_wave = generate_sine_wave(15000, 0.3)
        sd.play(beep_wave, samplerate=44100, blocking=True)
        time.sleep(3)
        pyautogui.typewrite(list(QApplication.clipboard().text()), 0.01)

    def on_transcript_changed(self):
        print("Transcript:", self.transcript_edit.toPlainText())
        self.transcription = self.transcript_edit.toPlainText()

    def tr(self):
        if not self.r:
            self.r = 1
            self.rec_btn.setStyleSheet(f"background-color: {colors['success']}")
            self.status_label.setText("Recording...")
            self.ad = []
            # Convert list to array for sounddevice
            self.st = sd.InputStream(callback=self.ac, channels=1, samplerate=self.sr)
            self.st.start()
        else:
            self.r = 0
            self.rec_btn.setStyleSheet(STYLESHEET)
            self.status_label.setText("Processing...")
            self.st and (self.st.stop(), self.st.close())
            self.pa()

    def ac(self, indata, frames, time, status):
        status and print(status)
        # Convert numpy array to list before appending
        if self.r:
            self.ad.append([float(x[0]) for x in indata])

    def pa(self):
        import soundfile as sf

        if not self.ad:
            self.status_label.setText("No audio data recorded")
            return
        # Flatten list of lists into single list
        audio_data = [sample for chunk in self.ad for sample in chunk]
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, self.sr, format='wav')
        audio_buffer.seek(0)
        self.transcribe_audio(audio_buffer)

    def transcribe_audio(self, af):
        logging.info("Transcribing audio ")
        self.status_label.setText("🎤🔁 Transcribing...")
        r = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            files={"file": ("audio.wav", af, "audio/wav")},
            data={"model": "whisper-large-v3", "temperature": 0, "response_format": "json", "language": "en"},
        )
        if r.status_code == 200:
            result = r.json()['text']
            logging.info(f"Transcription result: {result}")
        else:
            logging.error(f"Error during transcription: {r.status_code} - {r.text}")
        self.transcription = result
        self.status_label.setText(f"🟢Transcription Success")
        self.transcript_edit.setPlainText(self.transcription)

    def capture_screen(self):
        screen = QApplication.primaryScreen()
        self.screen_capture = screen.grabWindow(0)
        scaled_pixmap = self.screen_capture.scaled(self.screen_view.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.screen_view.setPixmap(scaled_pixmap)
        self.status_label.setText("Screen captured")

    def send_to_ai(self):

        logging.info("Sending to AI...")

        try:
            # Validate inputs
            if not self.screen_capture and not self.transcription:
                self.status_label.setText("Error: Please provide either an image or voiceover")
                return

            client = utils.get_client()
            self.status_label.setText("Sending to AI...")

            # Convert QPixmap to base64-encoded string if screen capture exists
            image_base64 = None
            if self.screen_capture:
                logging.info("Image in CTX")
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

            # use clipboard if selected
            clippy = ""
            if self.clipboard_checkbox.isChecked():
                logging.info("Appending Clipboard to CTX")
                clippy = f"<Clipboard>{QApplication.clipboard().text()}</Clipboard>"
                print(f"Clipboard: {clippy[:1000]}")

            router_info = utils.router(self.transcription)
            logging.info(f"Router Info: {router_info}")
            workspace_ctx = ""
            web_search_ctx = ""
            if router_info.get("docs_query", ""):
                self.workspace_checkbox.setChecked(True)
            if router_info.get("web_query", ""):
                self.websearch_checkbox.setChecked(True)

            if self.workspace_checkbox.isChecked():
                workspace_ctx = f"<workspace-results>{my_vdb.query(router_info.get("docs_query",''))}</workspace-results>"

            if self.websearch_checkbox.isChecked():
                web_search_ctx = f"<web-search> {utils.web_search(router_info.get("web_query"))} </web-search>"
                logging.info(
                    "Appended Webresults to CTX, Length:",
                )

            # time.sleep(5)
            # Build message content
            messages = [
                {
                    "role": "system",
                    "content": f"""You are helpful copilot. Always Give Detailed Outputs, well formatted markdown. easy to understand
                    
                    
                    # Contexts to refer from for better assist user query:
                    
                    {clippy}
                    {workspace_ctx}
                    {web_search_ctx}
                    
                    """.replace(
                        "\n\n", "\n"
                    ).replace(
                        "\t", " "
                    ),
                }
            ]

            if self.transcription:
                messages.append({"role": "user", "content": f"Transcript: {self.transcription}"})
            # Add image message if image exists
            if image_base64:
                messages[0]['role'] = "user"
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"text": "Analyze this image carefully and " + self.transcription, "type": "text"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                        ],
                    }
                )

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
                self.show_ai_response(ai_response)
                self.status_label.setText("Response Received From AI")

                # Copy response to clipboard
                # clipboard = QApplication.clipboard()
                # clipboard.setText(ai_response)

            except Exception as e:
                self.status_label.setText(f"API Error: {str(e)}")

        except Exception as e:
            self.status_label.setText(f"Critical error: {str(e)}")

    def show_ai_response(self, response):
        dialog = QDialog(self)
        dialog.setWindowTitle("AI's Response")
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(response)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        button_layout = QHBoxLayout()

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(response))
        button_layout.addWidget(copy_button)

        export_button = QPushButton("Export PDF")
        export_button.clicked.connect(lambda: self.export_artifact(response))
        button_layout.addWidget(export_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.resize(500, 400)
        dialog.exec()


    def export_artifact(self, markdown):
        try:
            self.status_label.setText("Exporting PDF...")
            pdf_content = utils.save_artifact(markdown)

            # Get suggested filename
            utils.suggest_filename(markdown)

            # Generate timestamp-based filename
            filename = f"artifact_{int(time.time())}.pdf"
            filepath = os.path.join(os.getenv('ARTIFACT_DIR', '.artifacts'), filename)

            # Save PDF file
            with open(filepath, 'wb') as f:
                f.write(pdf_content)

            self.status_label.setText(f"PDF exported to {filepath}")

        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")
            
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
