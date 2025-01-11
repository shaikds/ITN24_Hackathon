from scapy.all import *
import socket
import threading
import time

from scapy.layers.inet import IP, UDP

from OfferMessage import OfferMessage
from RequestMessage import RequestMessage
from States.ServerState import ServerState


class Server:
    serverState = None

    def __init__(self, ip, port):
        self.serverState = ServerState.OFFER
    def send_offer_broadcast():
        offer = OfferMessage(udp_port=5005, tcp_port=6006)  # Random example ports
        while True:
            send(IP(dst="255.255.255.255") / UDP(dport=13117) / Raw(load=offer.pack()), verbose=0)
            time.sleep(1)

    def handle_tcp_connection(conn):
        data = conn.recv(1024)
        request = RequestMessage.unpack(data)
        payload = b'a' * request.file_size
        conn.sendall(payload)
        conn.close()

    def handle_udp_request(data, client_address):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        request = RequestMessage.unpack(data)
        payload = b'a' * request.file_size
        udp_socket.sendto(payload, client_address)
        udp_socket.close()

    def tcp_server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 6006))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_tcp_connection, args=(conn,)).start()

    def udp_listener():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", 5005))
        while True:
            data, addr = s.recvfrom(1024)
            threading.Thread(target=handle_udp_request, args=(data, addr)).start()

if __name__ == "__main__":
    threading.Thread(target=send_offer_broadcast).start()
    threading.Thread(target=tcp_server).start()
    threading.Thread(target=udp_listener).start()
