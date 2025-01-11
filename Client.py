import logging

from OfferMessage import OfferMessage
from RequestMessage import RequestMessage

from scapy.all import *
import socket
import threading
import time
from enum import Enum


# Create an enum of Client states
class ClientState(Enum):
    STARTUP = "STARTUP"
    LOOKING_FOR_SERVER = "LOOKING_FOR_SERVER"
    SPEED_TEST = "SPEED_TEST"


class Client:
    # Declare a private field for handling client state
    __currState = None

    # Constructor
    def __init__(self):
        self.__currState = ClientState.STARTUP
        self.collect_user_input()

    def collect_user_input(self):
        # Immediately ask for user input upon starting the client
        print("Please configure your download parameters.")
        self.file_size = int(input("Enter the file size in bytes (e.g., 1000000000 for 1GB): "))
        self.tcp_connections = int(input("Enter the number of TCP connections: "))
        self.udp_connections = int(input("Enter the number of UDP connections: "))
        self.__currState = ClientState.LOOKING_FOR_SERVER
        print("Client started, listening for offer requests...")
        self.listen_for_offers()

    def listen_for_offers(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("", 13117))
        while True:
            data, addr = s.recvfrom(1024)
            try:
                # Got an offer
                offer = OfferMessage.unpack(data)
                print(f"Received offer from {addr[0]}")
                # Start Speed - Test .
                self.__currState = ClientState.SPEED_TEST
                self.initiate_downloads(offer, addr[0])
            except Exception as e:
                print(f"Error unpacking offer: {e}")
                # Modify state, and re-listen to offers again.
                self.__currState = ClientState.LOOKING_FOR_SERVER
                self.listen_for_offers()

    def initiate_downloads(self, offer, server_ip):
        threads = []
        for _ in range(self.tcp_connections):
            tcp_thread = threading.Thread(target=self.perform_tcp_download, args=(server_ip, offer.tcp_port))
            threads.append(tcp_thread)
            tcp_thread.start()

        for _ in range(self.udp_connections):
            udp_thread = threading.Thread(target=self.perform_udp_download, args=(server_ip, offer.udp_port))
            threads.append(udp_thread)
            udp_thread.start()

        for thread in threads:
            thread.join()

        print("All transfers complete, listening to offer requests again...")
        self.__currState = ClientState.LOOKING_FOR_SERVER
        self.listen_for_offers()

    def perform_tcp_download(self, server_ip, tcp_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, tcp_port))
            # Send the file size as a string followed by a newline as required.
            file_size_str = f"{self.file_size}\n"
            s.send(file_size_str.encode())  # Ensuring the message is correctly encoded.
            start_time = self.logStartTime()
            data = b''
            while True:
                part = s.recv(1024)
                if not part:
                    break
                data += part
            elapsed_time = time.time() - start_time
            speed = (len(data) * 8 / elapsed_time) if elapsed_time > 0 else 0
            print(
                f"TCP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second")

    def perform_udp_download(self, server_ip, udp_port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Send the file size in a request packet
            request = RequestMessage(file_size=self.file_size)
            s.sendto(request.pack(), (server_ip, udp_port))
            start_time = self.logStartTime()
            data = b''
            while True:
                part = s.recv(1024)
                if not part:
                    break
                data += part
            elapsed_time = time.time() - start_time
            speed = (len(data) * 8 / elapsed_time) if elapsed_time > 0 else 0
            print(
                f"UDP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second")



    # Log the start time immediately after sending the UDP request.
    def logStartTime(self):
        start_time = None # declaring
        start_time = time.time() # logging
        logging.log(f"Start time : {start_time.__str__()}")
        return start_time # return

if __name__ == "__main__":
    client = Client()
