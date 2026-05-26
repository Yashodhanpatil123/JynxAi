import sys
import requests

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QLineEdit
)

from PyQt6.QtGui import QPixmap

from PyQt6.QtCore import (
    Qt,
    QPoint,
    QThread,
    pyqtSignal,
    QTimer
)


# =========================================
# AI THREAD
# =========================================
class AIWorker(QThread):

    finished = pyqtSignal(str)

    def __init__(self, user_text):
        super().__init__()

        self.user_text = user_text

    def run(self):

        prompt = f"""
You are Jynx.

You are a cute anime AI desktop assistant.

Rules:
- Reply in 1 short sentence only
- Maximum 12 words
- Be emotional and cute
- Speak casually

User:
{self.user_text}
"""

        try:

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "phi3",
                    "prompt": prompt,
                    "stream": False,

                    "options": {
                        "num_predict": 30,
                        "temperature": 0.7
                    }
                }
            )

            data = response.json()

            reply = data["response"]

        except Exception as e:

            print("Ollama Error:", e)

            reply = "I'm sleepy..."

        self.finished.emit(reply)


# =========================================
# MAIN WINDOW
# =========================================
class JynxWindow(QWidget):

    def __init__(self):
        super().__init__()

        # =====================================
        # Window Settings
        # =====================================
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # =====================================
        # Character
        # =====================================
        self.character = QLabel(self)

        self.character_width = 350
        self.character_height = 500

        self.current_emotion = "idle"

        # =====================================
        # Speech Bubble
        # =====================================
        self.speech = QLabel(self)

        self.speech.setStyleSheet("""
            background-color: rgba(255,255,255,230);
            color: black;
            border-radius: 20px;
            padding: 15px;
            font-size: 18px;
            font-weight: bold;
        """)

        self.speech.setWordWrap(True)

        self.speech.resize(320, 180)

        self.speech.move(250, 40)

        self.speech.setText("Hello~")

        # =====================================
        # Input Box
        # =====================================
        self.input_box = QLineEdit(self)

        self.input_box.resize(320, 40)

        self.input_box.move(20, 520)

        self.input_box.setPlaceholderText(
            "Talk to Jynx..."
        )

        self.input_box.returnPressed.connect(
            self.handle_message
        )

        self.input_box.setFocus()

        # =====================================
        # Load Initial Expression
        # =====================================
        self.set_expression("idle")

        # =====================================
        # Window
        # =====================================
        self.resize(620, 620)

        self.base_x = 100
        self.base_y = 100

        self.move(self.base_x, self.base_y)

        self.old_pos = QPoint()

        # =====================================
        # FLOATING ANIMATION
        # =====================================
        self.float_offset = 0
        self.float_direction = 1

        self.float_timer = QTimer()

        self.float_timer.timeout.connect(
            self.float_animation
        )

        self.float_timer.start(40)

        # =====================================
        # BLINK TIMER
        # =====================================
        self.blink_timer = QTimer()

        self.blink_timer.timeout.connect(
            self.blink_animation
        )

        self.blink_timer.start(4000)

    # =====================================
    # FLOATING/BREATHING
    # =====================================
    def float_animation(self):

        self.float_offset += self.float_direction

        if self.float_offset > 10:
            self.float_direction = -1

        elif self.float_offset < -10:
            self.float_direction = 1

        self.character.move(
            0,
            self.float_offset
        )

    # =====================================
    # BLINK
    # =====================================
    def blink_animation(self):

        if self.current_emotion != "idle":
            return

        blink_pixmap = QPixmap(
            "assets/expressions/idle_blink.png"
        )

        blink_pixmap = blink_pixmap.scaled(
            self.character_width,
            self.character_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.character.setPixmap(blink_pixmap)

        QTimer.singleShot(
            150,
            lambda: self.set_expression("idle")
        )

    # =====================================
    # CHANGE EXPRESSION
    # =====================================
    def set_expression(self, emotion):

        self.current_emotion = emotion

        path = f"assets/expressions/{emotion}.png"

        pixmap = QPixmap(path)

        if pixmap.isNull():
            print(f"Missing image: {path}")
            return

        pixmap = pixmap.scaled(
            self.character_width,
            self.character_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.character.setPixmap(pixmap)

        self.character.resize(
            pixmap.width(),
            pixmap.height()
        )

    # =====================================
    # DETECT EMOTION
    # =====================================
    def detect_emotion(self, text):

        text = text.lower()

        if any(word in text for word in [
            "thank",
            "great",
            "nice",
            "awesome"
        ]):
            return "happy"

        elif any(word in text for word in [
            "love",
            "cute",
            "beautiful"
        ]):
            return "shy"

        elif any(word in text for word in [
            "hate",
            "stupid",
            "idiot"
        ]):
            return "angry"

        elif any(word in text for word in [
            "sad",
            "alone",
            "sorry"
        ]):
            return "sad"

        return "idle"

    # =====================================
    # HANDLE MESSAGE
    # =====================================
    def handle_message(self):

        user_text = self.input_box.text()

        if not user_text.strip():
            return

        emotion = self.detect_emotion(
            user_text
        )

        self.set_expression(emotion)

        self.speech.setText(
            "Thinking..."
        )

        self.worker = AIWorker(user_text)

        self.worker.finished.connect(
            self.show_reply
        )

        self.worker.start()

        self.input_box.clear()

        self.input_box.setFocus()

    # =====================================
    # SHOW REPLY
    # =====================================
    def show_reply(self, reply):

        self.speech.setText(reply)

        self.input_box.setFocus()

    # =====================================
    # DRAGGING
    # =====================================
    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.old_pos = (
                event.globalPosition().toPoint()
            )

    def mouseMoveEvent(self, event):

        if event.buttons() == Qt.MouseButton.LeftButton:

            delta = (
                event.globalPosition().toPoint()
                - self.old_pos
            )

            self.move(
                self.x() + delta.x(),
                self.y() + delta.y()
            )

            self.old_pos = (
                event.globalPosition().toPoint()
            )

    # =====================================
    # CLOSE
    # =====================================
    def mouseDoubleClickEvent(self, event):
        self.close()


# =========================================
# START APP
# =========================================
app = QApplication(sys.argv)

window = JynxWindow()

window.show()

sys.exit(app.exec())