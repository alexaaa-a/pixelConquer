import socket
import threading
import pickle
import struct
import time


class Room:
    def __init__(self, name):
        self.name = name
        self.clients = []
        self.client_data = {}
        self.colors = []
        self.game_over = False
        self.round_timer = None
        self.round_start_time = None
        self.field_state = {}
        self.stop_timer = False

    def add_client(self, client, name, color):
        self.clients.append(client)
        self.client_data[client] = {'name': name, 'color': color}

    def remove_client(self, client):
        if client not in self.client_data:
            print(f"Client {client} is not in the room.")
            return
        name = self.client_data[client]['name']
        if client in self.clients:
            del self.client_data[client]
            self.clients.remove(client)

            if len(self.clients) >= 2:
                self.broadcast({'type': 'chat', 'body': f'{name} left the game!'})
            else:
                for remaining_client in self.clients:
                    remaining_client.send_pickle({'type': 'chat', 'body': f'{name} left the game!'})
                    remaining_client.send_pickle({'type': 'end_game', 'body': ''})

                self.win()
                self.end_game()

    def broadcast(self, message, curr_client=None):
        for client in self.clients:
            if client != curr_client:
                try:
                    client.send_pickle(message)
                except Exception as e:
                    print(f"Error when sending a message to the client: {e}")

    def ready_for_game(self):
        cnt = 0
        for client in self.clients:
            if client.ready:
                cnt += 1

        return cnt > 1

    def start_game(self):
        if self.round_timer:
            self.clients[-1].send_pickle({'type': 'update', 'body': self.field_state})
            self.clients[-1].send_pickle({'type': 'start_game', 'body': 'Game started!'})
            self.clients[-1].send_pickle({'type': 'chat', 'body': "Game started! The round has begun!"})
            print("The game is already running!")
            return

        self.stop_timer = False
        self.broadcast({'type': 'start_game', 'body': 'Game started!'})
        self.broadcast({'type': 'chat', 'body': "Game started! The round has begun!"})
        self.round_start_time = time.time()
        self.round_timer = threading.Thread(target=self.run_timer, args=(300,))
        self.round_timer.start()

    def run_timer(self, duration):
        start_time = time.time()
        while not self.stop_timer and time.time() - start_time < duration + 1:
            remaining_time = duration - int(time.time() - start_time)
            self.broadcast({'type': 'timer', 'body': remaining_time})
            time.sleep(1)

        if not self.stop_timer:
            self.broadcast({'type': 'end_game', 'body': ""})
            self.win()
            self.end_game()

    def win(self):
        if self.game_over:
            return
        self.game_over = True

        max_cnt = -1
        win_clients = []

        for client in self.clients:
            if client.count > max_cnt:
                max_cnt = client.count

        for client in self.clients:
            if client.count == max_cnt:
                win_clients.append(client)

        for client in self.clients:
            if client in win_clients:
                client.send_pickle({
                    'type': 'chat',
                    'body': 'Game over! You win! A photo of the playing field has been sent to you!'
                })
            else:
                client.send_pickle({
                    'type': 'chat',
                    'body': 'Game over! You lose! A photo of the playing field has been sent to you!'
                })

    def end_game(self):
        self.stop_timer = True
        if self.round_timer and self.round_timer.is_alive():
            self.round_timer.join()

        self.clients = []
        self.client_data = {}
        self.colors = []
        self.game_over = False
        self.round_timer = None
        self.round_start_time = None
        self.field_state = {}
        self.stop_timer = False


class ClientThread(threading.Thread):
    def __init__(self, sock: socket.socket, addr, rooms):
        super().__init__()
        self.sock = sock
        self.addr = addr
        self.name = ''
        self.color = ''
        self.room = None
        self.rooms = rooms
        self.ready = False
        self.count = 0
        self.start()

    def run(self):
        try:
            while True:
                data = self.recv()
                if not data:
                    break

                print(f"Received data from {self.addr}: {data}")
                match data['type']:
                    case 'name':
                        self.name = data['body']
                        print(f"Client {self.addr} registered as {self.name}.")
                        names[self] = self.name
                        self.send_pickle({'type': 'chat', 'body': f"Welcome, {self.name}!"})
                    case 'color':
                        self.color = data['body']
                        self.room.colors.append(self.color)
                        print(f"{self.name} chose color {self.color}.")
                    case 'room':
                        self.join_room(data['body'])
                        self.send_pickle({'type': 'colors', 'body': self.room.colors})
                    case 'paint':
                        x, y, color = data['body']
                        print(f"{self.name} painted over the cell ({x}, {y}) in color {color}.")
                        self.room.field_state[(x, y)] = color
                        self.count += 1
                        if self.room:
                            self.room.broadcast({'type': 'paint', 'body': (x, y, color)}, self)
                    case 'chat':
                        message = f"{self.name}: {data['body']}"
                        msg_cl = f'You: {data["body"]}'
                        print(f"Message from room {self.room.name if self.room else 'N/A'}: {message}")
                        if self.room:
                            self.room.broadcast({'type': 'chat', 'body': message}, self)
                            self.send_pickle({'type': 'chat', 'body': msg_cl})
                    case 'ready':
                        self.ready = True
                        if self.room.ready_for_game():
                            self.room.broadcast({'type': 'start_game', 'body': 'Game started!'})
                            self.room.start_game()
                        else:
                            self.send_pickle({'type': 'not ready', 'body': 'Game not ready!'})
                    case 'quit':
                        self.disconnect()
                    case _:
                        print(f"Unknown message type: {data['type']}")
        finally:
            self.disconnect()

    def join_room(self, room_name):
        for room in self.rooms:
            if room.name == room_name:
                self.room = room
                room.add_client(self, self.name, self.color)
                print(f"{self.name} joined the room {room.name}.")

                if room.round_timer and not room.game_over:
                    elapsed_time = int(time.time() - room.round_start_time)
                    remaining_time = max(0, 300 - elapsed_time)
                    self.send_pickle({'type': 'timer', 'body': remaining_time})
                else:
                    room.round_timer = None
                    room.round_start_time = None

                return

        self.send_pickle({'type': 'chat', 'body': "The room was not found!"})

    def disconnect(self):
        print(f"Client {self.addr} has disconnected.")
        if self.room:
            self.room.remove_client(self)

    def send_pickle(self, data):
        try:
            serialized_data = pickle.dumps(data)
            self.sock.sendall(struct.pack("!I", len(serialized_data)))
            self.sock.sendall(serialized_data)
        except Exception as e:
            print(f"Error sending data to the client {self.addr}: {e}")
            self.disconnect()

    def recv(self):
        try:
            length_bytes = self.sock.recv(4)
            if not length_bytes:
                return None
            data_length = struct.unpack("!I", length_bytes)[0]
            data = b""
            while len(data) < data_length:
                packet = self.sock.recv(data_length - len(data))
                if not packet:
                    return None
                data += packet
            return pickle.loads(data)
        except Exception as e:
            print(f"Error receiving data from the client {self.addr}: {e}")
            return None


names = {}


class Server:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen()
        print('Server is running...')

        self.rooms = [
            Room('Pixel Paradise'), Room('Color Clash Arena'),
            Room('Pixel Pirates Bay'), Room('Monochrome Mayhem'),
            Room('Rainbow Rumble'), Room('Gridlock Galaxy'),
            Room('Palette Playground'), Room('Chromatic Chaos'),
            Room('Hue Hunters'), Room('Spectral Showdown')
        ]

    def serve_forever(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            print(f"The client has connected: {client_addr}")
            client_thread = ClientThread(client_sock, client_addr, self.rooms)
            client_thread.send_pickle({'type': 'names', 'body': list(names.values())})


if __name__ == "__main__":
    server = Server(host='127.0.0.1', port=12345)
    server.serve_forever()
