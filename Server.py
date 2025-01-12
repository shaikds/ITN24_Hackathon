import socket
import threading
import time
from enum import Enum
from Constants import *
from OfferMessage import OfferMessage
from RequestMessage import RequestMessage
from PayloadMessage import PayloadMessage


class ServerState(Enum):
    RUNNING = 1
    SHUTDOWN = 2


class Server:
    """
    Multi-threaded server:
      - Broadcasts OFFER on UDP once every second
      - Listens for REQUEST on UDP
      - Accepts TCP connections
      - Sends file data via TCP or UDP
    """

    def __init__(self, server_ip="172.1.0.4", udp_port=DEFAULT_UDP_PORT, tcp_port=DEFAULT_TCP_PORT):
        """
        server_ip: The IP address that we want to display in the startup print.
        """
        self.server_ip = server_ip
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.state = ServerState.RUNNING
        self.stop_broadcast_event = threading.Event()
        self.udp_socket = None
        self.tcp_socket = None

    def start(self):
        print(f"Server started, listening on IP address {self.server_ip}")

        # Thread for sending OFFER broadcasts
        broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        broadcast_thread.start()

        # Thread for listening on UDP for REQUEST messages
        udp_listen_thread = threading.Thread(target=self._listen_udp_requests, daemon=True)
        udp_listen_thread.start()

        # Start TCP in the main thread (or another thread if you prefer)
        self._start_tcp_server()

    def stop(self):
        self.state = ServerState.SHUTDOWN
        self.stop_broadcast_event.set()
        if self.udp_socket:
            self.udp_socket.close()
        if self.tcp_socket:
            self.tcp_socket.close()

    def _broadcast_loop(self):
        """
        Broadcast an OfferMessage every second until stopped.
        """
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        while not self.stop_broadcast_event.is_set():
            offer = OfferMessage(self.udp_port, self.tcp_port)
            data = offer.encode()
            self.udp_socket.sendto(data, (BROADCAST_IP, self.udp_port))
            time.sleep(BROADCAST_INTERVAL)

    def _listen_udp_requests(self):
        """
        Listen for RequestMessage on UDP.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("", self.udp_port))

        while self.state == ServerState.RUNNING:
            try:
                data, addr = sock.recvfrom(4096)
                if len(data) < 13:
                    # Too short to be a valid RequestMessage
                    continue

                req = RequestMessage.decode(data)
                if req is None:
                    continue

                # Start a thread to handle the UDP data transfer
                threading.Thread(
                    target=self._handle_udp_transfer,
                    args=(sock, addr, req.file_size),
                    daemon=True
                ).start()
            except ValueError:
                continue
            except OSError:
                break

    def _handle_udp_transfer(self, sock, client_addr, file_size):
        """
        Send file_size bytes over UDP in segments.
        """
        segment_size = 1024
        total_segments = (file_size + segment_size - 1) // segment_size

        sent_bytes = 0
        for seg_num in range(total_segments):
            chunk_size = min(segment_size, file_size - sent_bytes)
            chunk_data = b'x' * chunk_size

            pm = PayloadMessage(total_segments, seg_num, chunk_data)
            sock.sendto(pm.encode(), client_addr)

            sent_bytes += chunk_size

    def _start_tcp_server(self):
        """
        Accept TCP connections, read file size, send that many bytes.
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.tcp_socket.bind(("", self.tcp_port))
        self.tcp_socket.listen(5)

        while self.state == ServerState.RUNNING:
            try:
                client_sock, addr = self.tcp_socket.accept()
                threading.Thread(
                    target=self._handle_tcp_client,
                    args=(client_sock,),
                    daemon=True
                ).start()
            except OSError:
                break

    def _handle_tcp_client(self, client_sock):
        """
        1. Receive ASCII line => file size
        2. Send that many bytes
        """
        try:
            request_str = b''
            while True:
                chunk = client_sock.recv(1)
                if not chunk:
                    break
                request_str += chunk
                if request_str.endswith(b"\n"):
                    break

            file_size = int(request_str.decode().strip())
            data_to_send = b'y' * file_size
            client_sock.sendall(data_to_send)
        except:
            pass
        finally:
            client_sock.close()


if __name__ == "__main__":
    server = Server(server_ip="172.1.0.4")
    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
