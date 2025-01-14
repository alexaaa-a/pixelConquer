from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QIcon

from color_window_ui import Ui_MainColor
import socket
import pickle
from threading import Thread
from queue import SimpleQueue
from reg_ui import Ui_MainWindow
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject, QTimer, QRectF
from PyQt6.QtWidgets import QApplication, QMainWindow, QColorDialog, \
    QGraphicsScene, QGraphicsRectItem
import struct
from room_ui import Ui_MainRoom
from game_ui import Ui_MainGame


class Communication(QObject):
    chat_signal = pyqtSignal(str)
    game_signal = pyqtSignal(int, int, str)
    start_game_signal = pyqtSignal()
    end_game_signal = pyqtSignal()
    timer_signal = pyqtSignal(int)

class Registration(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.room = None
        self.setupUi(self)
        self.communication = Communication()
        self.sock_comm = Socket('127.0.0.1', 12345, self.communication)
        self.setWindowTitle('Registration')
        self.lineEdit.setPlaceholderText('Enter your name...')
        self.send_room.setEnabled(False)
        self.send_room.clicked.connect(self.send)
        self.check_name.clicked.connect(self.check)
        self.setWindowIcon(QIcon('reg_icon.jpg'))

        self.show()

    @pyqtSlot()
    def check(self):
        if self.lineEdit.text() == '':
            self.status.setText('Please enter a name!')
        elif self.lineEdit.text() not in self.sock_comm.names:
            self.status.setText('Available name!')
            self.send_room.setEnabled(True)
        else:
            self.status.setText('Wrong name! This name is already taken!')

    @pyqtSlot()
    def send(self):
        name = self.lineEdit.text()
        self.lineEdit.clear()
        self.status.setText(' ')
        self.sock_comm.queue.put({'type': 'name', 'body': name})
        self.hide()
        self.room = Room(self, name, self.communication, self.sock_comm)


class Room(QMainWindow, Ui_MainRoom):
    def __init__(self, main_window, name: str, communication: Communication, sock_comm: 'Socket'):
        super().__init__()
        self.name = name
        self.communication = communication
        self.sock_comm = sock_comm
        self.main_window = main_window
        self.setupUi(self)
        self.setWindowTitle(f'Hello, {name}!')
        self.setWindowIcon(QIcon('room_icon.jpg'))
        self.comboBox.addItems(['Pixel Paradise', 'Color Clash Arena',
                                'Pixel Pirates Bay', 'Monochrome Mayhem',
                                'Rainbow Rumble', 'Gridlock Galaxy',
                                'Palette Playground', 'Chromatic Chaos', 'Hue Hunters',
                                'Spectral Showdown'])
        self.room = ''
        self.show()
        self.pushButton.clicked.connect(self.color)
        self.pushButton_2.clicked.connect(self.exit_game)

    def color(self):
        self.room = self.comboBox.currentText()
        self.sock_comm.queue.put({'type': 'room', 'body': self.room})
        self.hide()
        self.choose_color = Color(self.main_window, self.name, self.communication, self.sock_comm, self.room)

    def exit_game(self):
        self.sock_comm.sock.close()
        self.hide()


class Color(QMainWindow, Ui_MainColor):
    def __init__(self, main_window, name: str, communication: Communication, sock_comm: 'Socket', room):
        super().__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.name = name
        self.communication = communication
        self.sock_comm = sock_comm
        self.room = room
        self.setWindowTitle(room)
        self.setWindowIcon(QIcon('color_icon.jpg'))
        self.show()

        self.color = None

        self.pushButton_2.setEnabled(False)

        self.pushButton.clicked.connect(self.choose)
        self.pushButton_2.clicked.connect(self.join_game)

    def choose(self):
        color = QColorDialog.getColor()
        if color.isValid() and color.name() not in self.sock_comm.colors and color != QColor('white'):
            self.label.setText('')
            self.color = color
            self.sock_comm.queue.put({'type': 'color', 'body': color.name()})
            self.label.setStyleSheet(f"background-color: {color.name()};")
            self.pushButton_2.setEnabled(True)
        else:
            self.label.setText('This color is invalid. It is already in use.')
            self.label.setStyleSheet(f"background-color: {QColor('red')};")

    def join_game(self):
        if self.color is None or not self.color.isValid():
            print("Error: color is not chosen or incorrect.")
            return
        print(f"Chosen color: {self.color.name()}")
        game = PixelGame(self.main_window, self.name, self.communication, self.sock_comm, self.color, self.room)
        print("Game's window is created, we hide color's window.")
        self.sock_comm.queue.put({'type': 'ready', 'body': 'yes'})
        self.hide()


class GridCell(QGraphicsRectItem):
    def __init__(self, x, y, size, color_callback):
        super().__init__(x * size, y * size, size, size)
        self.setBrush(QBrush(QColor('white')))
        self.setPen(QColor('black'))
        self.x = x
        self.y = y
        self.color_callback = color_callback

    def mousePressEvent(self, event):
        self.color_callback(self.x, self.y, self)


class PixelGame(QMainWindow, Ui_MainGame):
    def __init__(self, main_window: QMainWindow, username: str, communication: Communication, sock_comm: 'Socket', color, room):
        super().__init__()
        self.setupUi(self)
        print(f"PixelGame with color: {color.name()}")
        self.main_window = main_window
        self.username = username
        self.communication = communication
        self.sock_comm = sock_comm
        self.color = color
        self.room = room
        self.setWindowTitle(f'Pixel Conquer. {self.room}')
        self.setWindowIcon(QIcon('game_icon.jpg'))
        self.chat_history = []

        print(f"Game started with color: {color.name()}")
        self.show()
        self.scene = QGraphicsScene()
        self.game_field.setScene(self.scene)

        self.cell_size = 20
        self.grid_data = {}

        self.start_x = -50
        self.start_y = -50
        self.end_x = 50
        self.end_y = 50

        self.populate_grid(self.start_x, self.start_y, self.end_x, self.end_y)
        self.game_field.setSceneRect(
            self.start_x * self.cell_size,
            self.start_y * self.cell_size,
            (self.end_x - self.start_x) * self.cell_size,
            (self.end_y - self.start_y) * self.cell_size,
        )

        self.game_field.verticalScrollBar().valueChanged.connect(self.handle_scroll)
        self.game_field.horizontalScrollBar().valueChanged.connect(self.handle_scroll)
        self.pushButton.clicked.connect(self.change_room)
        self.send_btn.clicked.connect(self.btn_send)
        self.remaining_time = None

        self.communication.chat_signal.connect(self.chat_updating)
        self.communication.game_signal.connect(self.update_cell)
        self.communication.start_game_signal.connect(self.start_game)
        self.communication.end_game_signal.connect(self.end_game)
        self.communication.timer_signal.connect(self.update_timer)
        print("Signals done.")

    @pyqtSlot(int, int, int, int)
    def populate_grid(self, start_x, start_y, end_x, end_y):
        grid_buffer = 20
        self.start_x = start_x - grid_buffer
        self.start_y = start_y - grid_buffer
        self.end_x = end_x + grid_buffer
        self.end_y = end_y + grid_buffer

        for x in range(self.start_x, self.end_x):
            for y in range(self.start_y, self.end_y):
                if (x, y) not in self.grid_data:
                    cell = GridCell(x, y, self.cell_size, self.cell_clicked)
                    self.scene.addItem(cell)
                    self.grid_data[(x, y)] = cell

    @pyqtSlot(int, int, str)
    def update_cell(self, x, y, color_name):
        if (x, y) in self.grid_data:
            cell = self.grid_data[(x, y)]
            cell.setBrush(QBrush(QColor(color_name)))
            print(f'Ячейка ({x}, {y}) обновлена цветом {color_name}.')
        else:
            print(f"Ошибка: ячейка ({x}, {y}) не найдена в grid_data.")

    @pyqtSlot()
    def handle_scroll(self):
        visible_rect = self.game_field.viewport().rect()
        view_top_left = self.game_field.mapToScene(visible_rect.topLeft())
        view_bottom_right = self.game_field.mapToScene(visible_rect.bottomRight())

        visible_start_x = int(view_top_left.x() // self.cell_size)
        visible_start_y = int(view_top_left.y() // self.cell_size)
        visible_end_x = int(view_bottom_right.x() // self.cell_size)
        visible_end_y = int(view_bottom_right.y() // self.cell_size)

        if visible_start_x < self.start_x or visible_start_y < self.start_y or \
                visible_end_x > self.end_x or visible_end_y > self.end_y:
            self.populate_grid(visible_start_x, visible_start_y, visible_end_x, visible_end_y)

    @pyqtSlot(int, int, QGraphicsRectItem)
    def cell_clicked(self, x, y, rect):
        try:
            current_color = rect.brush().color().name()
            if current_color != QColor('white').name():
                print("Cell has already updated.")
                return

            if self.sock_comm.ready == False:
                return

            rect.setBrush(QBrush(self.color))
            self.grid_data[(x, y)] = self.color.name()

            self.sock_comm.queue.put({'type': 'paint', 'body': (x, y, self.color.name())})
            print(f"Cell ({x}, {y}) updated by you with color {self.color.name()}!")
        except Exception as e:
            print(f"Error with click: {e}")

    @pyqtSlot()
    def start_game(self):
        print("Game started!")

    @pyqtSlot()
    def btn_send(self):
        text = self.msg.text()
        if text.strip():
            self.sock_comm.queue.put({'type': 'chat', 'body': text})
            self.msg.clear()

    @pyqtSlot(str)
    def chat_updating(self, txt: str):
        self.chat_history.append(txt)
        self.game_chat.setText('\n'.join(self.chat_history))

    @pyqtSlot(int)
    def update_timer(self, remaining_time):
        self.remaining_time = remaining_time
        self.label.setText(f"Time: {self.remaining_time} seconds")
        if self.remaining_time <= 0:
            self.end_game()

    @pyqtSlot()
    def change_room(self):
        self.save_game_as_image()
        self.sock_comm.ready = False
        self.sock_comm.queue.put({'type': 'quit', 'body': ''})
        self.communication.chat_signal.disconnect()
        self.communication.game_signal.disconnect()
        self.communication.start_game_signal.disconnect()
        self.communication.end_game_signal.disconnect()
        self.communication.timer_signal.disconnect()
        self.close()
        self.main_window.show()

    @pyqtSlot()
    def end_game(self):
        self.label.setText("Game over! Return to room selection after 20 seconds.")
        self.pushButton.setEnabled(False)
        self.send_btn.setEnabled(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.change_room)
        self.timer.setSingleShot(True)
        self.timer.start(20000)

    @pyqtSlot()
    def save_game_as_image(self):
        visible_rect = self.game_field.rect()
        image = QImage(visible_rect.width(), visible_rect.height(), QImage.Format.Format_RGB32)

        painter = QPainter(image)

        self.game_field.render(painter, QRectF(image.rect()), visible_rect)
        painter.end()

        image_path = f"{self.username}_game.png"
        image.save(image_path)


class Socket:
    def __init__(self, host, port, communication: Communication):
        self.queue = SimpleQueue()
        self.communication = communication
        self.ready = False
        self.names = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        Thread(target=self.send_pickle_thread, daemon=True).start()
        Thread(target=self.rec_pickle_thread, daemon=True).start()

    def send_pickle_thread(self):
        while True:
            data = self.queue.get()
            serialized_data = pickle.dumps(data)
            data_length = len(serialized_data)
            print(f"Send data: {data}, length: {data_length}")
            self.sock.sendall(struct.pack("!I", data_length))
            self.sock.sendall(serialized_data)

    def rec_pickle(self):
        length_bytes = self.sock.recv(4)
        if not length_bytes:
            print("Error: couldn't get the length of the data.")
            return None
        data_length = struct.unpack("!I", length_bytes)[0]
        print(f"We are expecting data of length: {data_length}")

        data = b""
        while len(data) < data_length:
            packet = self.sock.recv(data_length - len(data))
            if not packet:
                print("Error: the connection is terminated.")
                return None
            data += packet

        deserialized_data = pickle.loads(data)
        print(f"Data received: {deserialized_data}")
        return deserialized_data

    def rec_pickle_thread(self):
        while True:
            try:
                data = self.rec_pickle()
                if data is None:
                    continue

                type = data['type']
                body = data['body']

                if type == 'chat':
                    self.communication.chat_signal.emit(body)
                elif type == 'start_game':
                    self.communication.start_game_signal.emit()
                    self.ready = True
                elif type == 'paint':
                    x, y, color_str = body
                    color = QColor(color_str)
                    self.communication.game_signal.emit(x, y, color.name())
                elif type == 'colors':
                    self.colors = body
                elif type == 'names':
                    self.names = body
                elif type == 'end_game':
                    self.communication.end_game_signal.emit()
                elif type == 'timer':
                    self.communication.timer_signal.emit(body)
                elif type == 'update':
                    field_state = body
                    for (x, y), color in field_state.items():
                        self.communication.game_signal.emit(x, y, color)
                else:
                    continue
            except Exception as e:
                print(f"Error in the data receipt flow: {e}")
                break


app = QApplication([])
window = Registration()
app.exec()