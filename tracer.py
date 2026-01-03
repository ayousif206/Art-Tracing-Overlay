from sys import argv, exit
##, _MEIPASS
from keyboard import add_hotkey, remove_hotkey, unhook, hook
from os import path
from math import ceil
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QShortcut
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QCursor, QKeySequence, QPixmap, QPainter, QColor, QIcon, QGuiApplication, QImage
from requests import get
from io import BytesIO
from urllib.parse import urlparse

class ImageTracer(QMainWindow):
    toggle_interact_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yuser")

        ## base_path = _MEIPASS
        ## icon_path = path.join(base_path, "yes.ico")
        ## self.setWindowIcon(QIcon(icon_path))

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.opacity = 255
        self.prev_opacity = 255
        self.bgcolorR = 10
        self.bgcolorG = 10
        self.bgcolorB = 10
        self.cminimumWidth = 333
        self.image_path = None
        self.interactable = True
        self.inspector_mode = False
        self.imageavailable = False
        self.currentpixmap = None
        self.is_visible = True
        self.changing = False
        self.keybind = 'insert'
        self.origWidth = 0.0
        self.origHeight = 0.0

        self.initUI()

        self.toggle_interact_signal.connect(self.do_toggle_interactability)
        add_hotkey(self.keybind, self.emit_toggle_signal, suppress=True)

    def emit_toggle_signal(self):
        self.toggle_interact_signal.emit()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_area = QWidget(self)
        layout.addWidget(self.image_area, stretch=1)

        self.button_frame = QFrame(self)
        self.button_frame.setFrameShape(QFrame.NoFrame)
        self.button_frame.setStyleSheet("background-color: rgba(10, 10, 10, 1)")

        self.button_frame.setAcceptDrops(True)
        self.button_frame.dragEnterEvent = self.button_frame_dragEnterEvent
        self.button_frame.dropEvent = self.button_frame_dropEvent

        self.drag_pos = None

        def frame_mouse_press(event):
            if event.button() == Qt.LeftButton:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        def frame_mouse_move(event):
            if event.buttons() == Qt.LeftButton and self.drag_pos:
                self.move(event.globalPos() - self.drag_pos)
                event.accept()

        def frame_mouse_release(event):
            self.drag_pos = None
            event.accept()

        self.button_frame.mousePressEvent = frame_mouse_press
        self.button_frame.mouseMoveEvent = frame_mouse_move
        self.button_frame.mouseReleaseEvent = frame_mouse_release

        for button in self.button_frame.findChildren(QPushButton):
            button.setAttribute(Qt.WA_NoMousePropagation, True)

        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(10, 10, 10, 10)
        self.bottom_bar.setSpacing(5)
        self.bottom_bar.setAlignment(Qt.AlignCenter)

        def create_btn(text, func, shortcut_key):
            btn = QPushButton(text)
            btn.clicked.connect(func)
            btn.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
            self.bottom_bar.addWidget(btn)
            sc = QShortcut(QKeySequence(shortcut_key), self)
            sc.activated.connect(func)
            return btn, sc

        self.keybind_button, _ = create_btn("K", self.change_keybind, "K")
        self.open_button, _ = create_btn("O", self.open_image, "O")
        self.paste_button, _ = create_btn("C", self.clipboard, "C")
        self.inspector_button, _ = create_btn("H", self.toggle_inspector, "H")
        self.vanish_button, _ = create_btn("U", self.toggle_visibility, "U")
        self.opacity_decrement_button, _ = create_btn("D", self.decrement_opacity, "D")
        self.opacity_increment_button, _ = create_btn("I", self.increment_opacity, "I")
        self.scale_button_minus, _ = create_btn("-", self.decrease_window_size, "-")
        self.scale_button_plus, _ = create_btn("+", self.increase_window_size, "=")

        self.button_frame.setLayout(self.bottom_bar)
        layout.addWidget(self.button_frame)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.setMinimumSize(self.cminimumWidth, 0)

    def set_custom_cursor(self):
        size = 7
        cursor_pixmap = QPixmap(size, size)
        cursor_pixmap.fill(Qt.transparent)
        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(0, 0, size - 1, size - 1)
        painter.end()
        cursor = QCursor(cursor_pixmap, size // 2, size // 2)
        self.setCursor(cursor)

    def enterEvent(self, event):
        self.set_custom_cursor()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def button_frame_dragEnterEvent(self, event):
        supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        mime = event.mimeData()

        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(supported_extensions):
                        event.acceptProposedAction()
                        return
                else:
                    url_str = url.toString()
                    parsed = urlparse(url_str)
                    if parsed.path.lower().endswith(supported_extensions):
                        event.acceptProposedAction()
                        return
        if mime.hasText():
            text = mime.text().strip()
            if text.lower().startswith('http'):
                parsed = urlparse(text)
                if parsed.path.lower().endswith(supported_extensions):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def button_frame_dropEvent(self, event):
        supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
        mime = event.mimeData()
        url = None

        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                if urls[0].isLocalFile():
                    file_path = urls[0].toLocalFile()
                    if file_path.lower().endswith(supported_extensions):
                        self.open_image_file(file_path)
                        event.acceptProposedAction()
                        return
                else:
                    url_str = urls[0].toString()
                    parsed = urlparse(url_str)
                    if parsed.path.lower().endswith(supported_extensions):
                        url = url_str
        elif mime.hasText():
            url_str = mime.text().strip()
            if url_str.lower().startswith('http'):
                parsed = urlparse(url_str)
                if parsed.path.lower().endswith(supported_extensions):
                    url = url_str

        if url:
            self.open_remote_image(url)
            event.acceptProposedAction()
        else:
            event.ignore()

    def open_remote_image(self, url):
        try:
            response = get(url, timeout=5)
            response.raise_for_status()
            image_data = BytesIO(response.content)

            image = QImage()
            if not image.loadFromData(image_data.read()):
                return
            
            pixmap = QPixmap.fromImage(image)
            self.load_pixmap(pixmap)
        except Exception:
            pass

    def open_image_file(self, file_path):
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.image_path = file_path
                self.load_pixmap(pixmap)

    def load_pixmap(self, pixmap):
        self.is_visible = True
        self.opacity = 255
        self.imageavailable = True
        self.currentpixmap = pixmap
        self.handle_avg_color(pixmap)

        new_width, new_height = pixmap.width(), pixmap.height()
        button_frame_height = self.button_frame.sizeHint().height()
        self.origWidth = float(new_width)
        self.origHeight = float(new_height + button_frame_height)

        if ceil(new_width) < self.cminimumWidth:
            factor = self.cminimumWidth / new_width
            new_height = new_height * factor
            self.origWidth = float(self.cminimumWidth)
            self.origHeight = float(new_height + button_frame_height)
            new_height = ceil(new_height)

        new_x = self.x()            
        new_y = self.y() + (self.height() - ceil(self.origHeight))
        self.setGeometry(new_x, new_y, ceil(self.origWidth), ceil(self.origHeight))
        self.update()

    def calculate_average_color(self, pixmap):
        image = pixmap.toImage().scaled(1, 1).convertToFormat(QImage.Format_RGB32)
        color = image.pixelColor(0, 0)
        self.bgcolorR = color.red()
        self.bgcolorG = color.green()
        self.bgcolorB = color.blue()

    def set_hotkey(self, key):
        try:
            remove_hotkey(self.keybind)
        except:
            pass
        self.keybind = key
        add_hotkey(self.keybind, self.emit_toggle_signal, suppress=True)
        self.changing = not self.changing
        self.keybind_button.setText("K")
        self.update()

    def change_keybind(self):
        self.changing = not self.changing
        self.keybind_button.setText("...")
        self.update()

        def key_event(event):
            unhook(key_event)
            self.set_hotkey(event.name)

        hook(key_event)

    def toggle_visibility(self):
        if self.imageavailable:
            self.is_visible = not self.is_visible
            if self.is_visible:
                self.opacity = self.prev_opacity
                self.vanish_button.setText("U")
            else:
                self.prev_opacity = self.opacity
                self.opacity = 0
                self.vanish_button.setText("S")
            self.update()

    def handle_avg_color(self, pixmap):
        self.calculate_average_color(pixmap)
        opacity = 0.15 if self.interactable else 0
        self.set_button_opacity(opacity)
    
    def clipboard(self):
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            image = clipboard.image()
            pixmap = QPixmap.fromImage(image)
            self.load_pixmap(pixmap)

    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.bmp *.jpeg *.webp);;All Files (*.*)"
        )
        if file_name:
            self.open_image_file(file_name)

    def toggle_inspector(self):
        if self.imageavailable:
            self.inspector_mode = not self.inspector_mode
            self.inspector_button.setText("A" if self.inspector_mode else "H")

    def mousePressEvent(self, event):
        if self.inspector_mode and self.currentpixmap:
            clicked_point = event.pos()
            image_rect = self.image_area.geometry() 
            if image_rect.contains(clicked_point):
                scale_x = self.currentpixmap.width() / image_rect.width()
                scale_y = self.currentpixmap.height() / image_rect.height()
                img_x = int(clicked_point.x() * scale_x)
                img_y = int(clicked_point.y() * scale_y)

                if 0 <= img_x < self.currentpixmap.width() and 0 <= img_y < self.currentpixmap.height():
                    color = self.currentpixmap.toImage().pixelColor(img_x, img_y)
                    hex_color = color.name()
                    QGuiApplication.clipboard().setText(hex_color[1:])

    def decrement_opacity(self):
        if self.imageavailable and self.is_visible:
            self.opacity = max(15, self.opacity - 15)
            self.update()

    def increment_opacity(self):
        if self.imageavailable:
            if not self.is_visible: 
                self.toggle_visibility()
            self.opacity = min(255, self.opacity + 15)
            self.update()

    def do_toggle_interactability(self):
        self.interactable = not self.interactable
        
        flags = Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint
        if not self.interactable:
            flags |= Qt.WindowTransparentForInput
        
        self.setWindowFlags(flags)
        self.show()

        if self.interactable and self.imageavailable:
            self.setFocusPolicy(Qt.StrongFocus)
            self.paste_button.setText("C")
            self.inspector_button.setText("A" if self.inspector_mode else "H")
            self.vanish_button.setText("U" if self.is_visible else "S")
            self.keybind_button.setText("A" if self.changing else "K")
            self.open_button.setText("O")
            self.opacity_decrement_button.setText("D")
            self.opacity_increment_button.setText("I")
            self.scale_button_minus.setText("-")
            self.scale_button_plus.setText("+")
            self.set_button_opacity(0.15)
            
        elif not self.interactable and self.imageavailable:
            self.setFocusPolicy(Qt.NoFocus)
            for btn in self.button_frame.findChildren(QPushButton):
                btn.setText("")
            self.set_button_opacity(0)

    def set_button_opacity(self, opacity):
        brightness = 0.299 * self.bgcolorR + 0.587 * self.bgcolorG + 0.114 * self.bgcolorB
        text_color = "0,0,0" if brightness >= 128 else "255,255,255"
        
        style = f"background-color: rgba({text_color}, {opacity}); border-radius: 8px; padding: 5px 10px; color: rgb({text_color})"
        
        for btn in self.button_frame.findChildren(QPushButton):
            btn.setStyleSheet(style)

        frame_opacity = 1 if opacity > 0 else 0
        self.button_frame.setStyleSheet(f"background-color: rgba({self.bgcolorR}, {self.bgcolorG}, {self.bgcolorB}, {frame_opacity})")
        
    def decrease_window_size(self):
        if self.imageavailable:
            self.apply_scale(0.9)
            
    def increase_window_size(self):
        if self.imageavailable:
            self.apply_scale(1.0/0.9)

    def apply_scale(self, factor):
        new_width = self.origWidth * factor
        new_height = self.origHeight * factor
        
        if ceil(new_width) < self.cminimumWidth:
            return

        self.origWidth = float(new_width)
        self.origHeight = float(new_height)
        
        current_geo = self.geometry()
        new_geo_h = ceil(self.origHeight)
        new_geo_w = ceil(self.origWidth)
        new_y = current_geo.y() + (current_geo.height() - new_geo_h)
        
        self.setGeometry(current_geo.x(), new_y, new_geo_w, new_geo_h)

    def paintEvent(self, event):
        if self.imageavailable and self.is_visible:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            op_val = max(0, min(255, self.opacity)) / 255.0
            painter.setOpacity(op_val)
            
            button_frame_height = self.button_frame.height()
            img_height = self.height() - button_frame_height
            
            painter.drawPixmap(0, 0, self.width(), img_height, self.currentpixmap)
            
if __name__ == '__main__':
    app = QApplication(argv)
    window = ImageTracer()
    window.show()
    exit(app.exec_())
