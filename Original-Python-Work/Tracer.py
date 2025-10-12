from sys import argv, exit
##, _MEIPASS
from keyboard import add_hotkey, remove_hotkey, unhook, hook
from os import path
from math import ceil
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QShortcut
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QCursor, QKeySequence, QPixmap, QPainter, QColor, QIcon, QGuiApplication, QImage
from requests import get
from io import BytesIO
from urllib.parse import urlparse

class ImageTracer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yuser")

##        base_path = _MEIPASS
##        icon_path = path.join(base_path, "yes.ico")
##        self.setWindowIcon(QIcon(icon_path))

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.opacity = 255
        self.bgcolorR = 10
        self.bgcolorG = 10
        self.bgcolorB = 10
        self.cminimumWidth = 333
        self.image_path = None
        self.interactable = True
        self.buttons_visible = True
        self.inspector_mode = False
        self.imageavailable = False
        self.currentpixmap = None
        self.vanished = False
        self.displayed = False
        self.changing = False
        self.keybind = 'insert'
        self.origWidth = 0.0
        self.origHeight = 0.0

        self.initUI()

        add_hotkey(self.keybind, self.toggle_interactability, suppress=True)

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

            def block_drag_event(event):
                event.ignore()

            button.mousePressEvent = block_drag_event
            button.mouseMoveEvent = block_drag_event
        
        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(10, 10, 10, 10)
        self.bottom_bar.setSpacing(5)
        self.bottom_bar.setAlignment(Qt.AlignCenter)

        self.keybind_button = QPushButton("K")
        self.keybind_button.clicked.connect(self.change_keybind)
        self.keybind_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.keybind_button)

        self.sh_keybind_button = QShortcut(QKeySequence("K"), self)
        self.sh_keybind_button.activated.connect(self.change_keybind)

        self.open_button = QPushButton("O")
        self.open_button.clicked.connect(self.open_image)
        self.open_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.open_button)

        self.sh_open_button = QShortcut(QKeySequence("O"), self)
        self.sh_open_button.activated.connect(self.open_image)

        self.paste_button = QPushButton("C")
        self.paste_button.clicked.connect(self.clipboard)
        self.paste_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.paste_button)

        self.sh_paste_button = QShortcut(QKeySequence("C"), self)
        self.sh_paste_button.activated.connect(self.clipboard)

        self.inspector_button = QPushButton("H")
        self.inspector_button.clicked.connect(self.toggle_inspector)
        self.inspector_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.inspector_button)

        self.sh_inspector_button = QShortcut(QKeySequence("H"), self)
        self.sh_inspector_button.activated.connect(self.toggle_inspector)

        self.vanish_button = QPushButton("U")
        self.vanish_button.clicked.connect(self.vanish)
        self.vanish_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.vanish_button)

        self.sh_vanish_button = QShortcut(QKeySequence("U"), self)
        self.sh_vanish_button.activated.connect(self.vanish)

        self.display_button = QPushButton("V")
        self.display_button.clicked.connect(self.display)
        self.display_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.display_button)

        self.sh_display_button = QShortcut(QKeySequence("V"), self)
        self.sh_display_button.activated.connect(self.display)

        self.opacity_decrement_button = QPushButton("D")
        self.opacity_decrement_button.clicked.connect(self.decrement_opacity)
        self.opacity_decrement_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.opacity_decrement_button)

        self.sh_dec_button = QShortcut(QKeySequence("D"), self)
        self.sh_dec_button.activated.connect(self.decrement_opacity)

        self.opacity_increment_button = QPushButton("I")
        self.opacity_increment_button.clicked.connect(self.increment_opacity)
        self.opacity_increment_button.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.opacity_increment_button)

        self.sh_inc_button = QShortcut(QKeySequence("I"), self)
        self.sh_inc_button.activated.connect(self.increment_opacity)

        self.scale_button_minus = QPushButton("-")
        self.scale_button_minus.clicked.connect(self.decrease_window_size)
        self.scale_button_minus.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.scale_button_minus)

        self.sh_in_button = QShortcut(QKeySequence("-"), self)
        self.sh_in_button.activated.connect(self.decrease_window_size)

        self.scale_button_plus = QPushButton("+")
        self.scale_button_plus.clicked.connect(self.increase_window_size)
        self.scale_button_plus.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 5px 10px")
        self.bottom_bar.addWidget(self.scale_button_plus)

        self.sh_out_button = QShortcut(QKeySequence("="), self)
        self.sh_out_button.activated.connect(self.increase_window_size)

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
        response = get(url)
        response.raise_for_status()
        image_data = BytesIO(response.content)

        image = QImage()
        if not image.loadFromData(image_data.read()):
            return
        pixmap = QPixmap.fromImage(image)
        self.currentpixmap = pixmap
        self.imageavailable = True

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
        new_y = self.y() + (self.height() - (new_height + button_frame_height))
        self.setGeometry(new_x, new_y, new_width, new_height + button_frame_height)
        self.update()

    def open_image_file(self, file_path):
        if file_path:
            if self.vanished:
                self.vanish()
            if self.displayed:
                self.display()
            self.opacity = 255
            self.imageavailable = True
            self.image_path = file_path
            pixmap = QPixmap(self.image_path)
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
            new_y = self.y() + (self.height() - (new_height + button_frame_height))

            self.setGeometry(new_x, new_y, new_width, new_height + button_frame_height)
            self.update()

    def calculate_average_color(self, pixmap):
        image = pixmap.toImage().convertToFormat(QImage.Format_RGB32)

        width = image.width()
        height = image.height()

        total_r = 0
        total_g = 0
        total_b = 0
        num_pixels = width * height

        for y in range(height):
            for x in range(width):
                color = image.pixelColor(x, y)
                total_r += color.red()
                total_g += color.green()
                total_b += color.blue()

        self.bgcolorR = total_r // num_pixels
        self.bgcolorG = total_g // num_pixels
        self.bgcolorB = total_b // num_pixels

    def set_hotkey(self, key):
        remove_hotkey(self.keybind)
        self.keybind = key
        add_hotkey(self.keybind, self.toggle_interactability, suppress=True)
        self.changing = not self.changing
        self.keybind_button.setText("K")
        self.update()

    def change_keybind(self):
        self.changing = not self.changing
        self.keybind_button.setText("A")
        self.update()

        def key_event(event):
            new_key = event.name
            if new_key == self.keybind:
                return
            unhook(key_event)
            self.set_hotkey(new_key)

        hook(key_event)

    def vanish(self):
        if self.imageavailable:
            if self.displayed:
                self.display()
            self.vanished = not self.vanished
            if self.vanished:
                self.opacity = self.opacity - 9999999
                self.vanish_button.setText("N")
            else:
                self.opacity = self.opacity + 9999999
                self.vanish_button.setText("U")
            self.update()

    def display(self):
        if self.imageavailable:
            if self.vanished:
                self.vanish()
            self.displayed = not self.displayed
            if self.displayed:
                self.opacity = self.opacity + 9999999
                self.display_button.setText("N")
            else:
                self.opacity = self.opacity - 9999999
                self.display_button.setText("V")
            self.update()

    def handle_avg_color(self, pixmap):
        self.calculate_average_color(pixmap)
        if self.interactable:
            opacity = 0.15
        else:
            opacity = 0
        self.set_button_opacity(opacity)
    
    def clipboard(self):
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            if self.vanished:
                self.vanish()
            if self.displayed:
                self.display()
            self.opacity = 255
                
            image = clipboard.image()
            pixmap = QPixmap.fromImage(image)
            self.currentpixmap = pixmap
            self.imageavailable = True

            self.handle_avg_color(pixmap)
            
            new_width, new_height = pixmap.width(), pixmap.height()
            button_frame_height = self.button_frame.sizeHint().height()
            self.origWidth = float(new_width)
            self.origHeight = float(new_height + button_frame_height)
            
            if ceil(new_width) < self.cminimumWidth:
                factor = self.cminimumWidth/new_width
                new_height = new_height*factor
                self.origWidth = float(self.cminimumWidth)
                self.origHeight = float(new_height + button_frame_height)
                new_height = ceil(new_height)

            new_x = self.x()            
            new_y = self.y() + (self.height() - (new_height + button_frame_height))

            self.setGeometry(new_x, new_y, new_width, new_height + button_frame_height)
            self.update()

    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.bmp *.jpeg *.webp);;All Files (*.*)"
        )
        if file_name:
            self.open_image_file(file_name)

    def toggle_inspector(self):
        if self.imageavailable:
            self.inspector_mode = not self.inspector_mode
            if self.inspector_mode:
                self.inspector_button.setText("A")
            else:
                self.inspector_button.setText("H")

    def mousePressEvent(self, event):
        if self.inspector_mode:
            clicked_point = event.pos()

            image_rect = self.image_area.geometry() 
            if image_rect.contains(clicked_point):
                image_pos = clicked_point - image_rect.topLeft()

                scale_x = self.currentpixmap.width() / image_rect.width()
                scale_y = self.currentpixmap.height() / image_rect.height()

                img_x = int(image_pos.x() * scale_x)
                img_y = int(image_pos.y() * scale_y)

                if 0 <= img_x < self.currentpixmap.width() and 0 <= img_y < self.currentpixmap.height():
                    color = self.currentpixmap.toImage().pixel(img_x, img_y)
                    color = QColor(color)
                    hex_color = color.name()

                    QGuiApplication.clipboard().setText(hex_color[1:])

    def decrement_opacity(self):
        if self.imageavailable:
            if self.vanished:
                self.vanish()
            if self.displayed:
                self.display()
            self.opacity = max(0, self.opacity - 15)
            self.update()

    def increment_opacity(self):
        if self.imageavailable:
            if self.vanished:
                self.vanish()
            if self.displayed:
                self.display()
            self.opacity = min(255, self.opacity + 15)
            self.update()

    def toggle_interactability(self):
        self.interactable = not self.interactable
        self.setAttribute(Qt.WA_TransparentForMouseEvents, not self.interactable)

        if self.interactable and self.imageavailable:
            self.setFocusPolicy(Qt.StrongFocus)
            self.paste_button.setText("C")
            if self.inspector_mode:
                self.inspector_button.setText("A")
            else:
                self.inspector_button.setText("H")
            if self.vanished:
                self.vanish_button.setText("N")
            else:
                self.vanish_button.setText("U")
            if self.displayed:
                self.display_button.setText("N")
            else:
                self.display_button.setText("V")
            if self.changing:
                self.keybind_button.setText("A")
            else:
                self.keybind_button.setText("K")
            self.open_button.setText("O")
            self.opacity_decrement_button.setText("D")
            self.opacity_increment_button.setText("I")
            self.scale_button_minus.setText("-")
            self.scale_button_plus.setText("+")

            self.set_button_opacity(0.15)
            
        elif not self.interactable and self.imageavailable:
            self.setFocusPolicy(Qt.NoFocus)
            self.keybind_button.setText("")
            self.paste_button.setText("")
            self.inspector_button.setText("")
            self.vanish_button.setText("")
            self.open_button.setText("")
            self.opacity_decrement_button.setText("")
            self.opacity_increment_button.setText("")
            self.scale_button_minus.setText("")
            self.scale_button_plus.setText("")
            self.display_button.setText("")

            self.set_button_opacity(0)

    def set_button_opacity(self, opacity):
        brightness = 0.299 * self.bgcolorR + 0.587 * self.bgcolorG + 0.114 * self.bgcolorB
        if brightness < 128:
            opacity_str = f"background-color: rgba(255, 255, 255, {opacity}); border-radius: 8px; padding: 5px 10px"
        else:
            opacity_str = f"background-color: rgba(0, 0, 0, {opacity}); border-radius: 8px; padding: 5px 10px"
        self.inspector_button.setStyleSheet(opacity_str)
        self.paste_button.setStyleSheet(opacity_str)
        self.open_button.setStyleSheet(opacity_str)
        self.opacity_decrement_button.setStyleSheet(opacity_str)
        self.opacity_increment_button.setStyleSheet(opacity_str)
        self.scale_button_minus.setStyleSheet(opacity_str)
        self.scale_button_plus.setStyleSheet(opacity_str)
        self.vanish_button.setStyleSheet(opacity_str)
        self.keybind_button.setStyleSheet(opacity_str)
        self.display_button.setStyleSheet(opacity_str)
        if opacity > 0:
            opacity = 1
        self.button_frame.setStyleSheet(f"background-color: rgba({self.bgcolorR}, {self.bgcolorG}, {self.bgcolorB}, {opacity})")
        
    def decrease_window_size(self):
        if self.imageavailable:
            width, height = self.origWidth, self.origHeight
            new_width, new_height = width * 0.9, height * 0.9
            
            if ceil(new_width) < self.cminimumWidth:
                return

            self.origWidth = float(new_width)
            self.origHeight = float(new_height)
            
            new_x = self.x()
            new_y = self.y() + (ceil(height) - ceil(new_height))
            self.setGeometry(new_x, new_y, ceil(new_width), ceil(new_height))
            
    def increase_window_size(self):
        if self.imageavailable:
            width, height = self.origWidth, self.origHeight
            new_width, new_height = width / 0.9, height / 0.9
            
            self.origWidth = float(new_width)
            self.origHeight = float(new_height)
            
            new_x = self.x()
            new_y = self.y() - (ceil(new_height) - ceil(height))
            self.setGeometry(new_x, new_y, ceil(new_width), ceil(new_height))

    def paintEvent(self, event):
        if self.imageavailable:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setOpacity(self.opacity / 255.0)
            button_frame_height = self.button_frame.sizeHint().height()
            img_height = self.origHeight - button_frame_height
            painter.drawPixmap(0, 0, ceil(self.origWidth), ceil(img_height), self.currentpixmap)
            
if __name__ == '__main__':
    app = QApplication(argv)
    window = ImageTracer()
    window.show()

    exit(app.exec_())
