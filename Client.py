import logging
import socket
import threading
import time
from enum import Enum
from Constants import *
from OfferMessage import OfferMessage
from PayloadMessage import PayloadMessage
from RequestMessage import RequestMessage

# Setup basic configuration for logging
logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')


# We set logging to CRITICAL, so no debug/info logs clutter the console.

class ClientState(Enum):
    STARTUP = 1
    LOOKING_FOR_SERVER = 2
    SPEED_TEST = 3


class Client:
    """
    Multi-threaded client with states:
      1) STARTUP            -> Ask the user for file size, #TCP, #UDP
      2) LOOKING_FOR_SERVER -> Listen for Offer
      3) SPEED_TEST         -> Perform TCP and UDP transfers in parallel
    """

    def __init__(self, file_size=1000000, num_tcp=1, num_udp=1):
        self.state = ClientState.STARTUP
        self.file_size = file_size
        self.num_tcp = num_tcp
        self.num_udp = num_udp

        self.server_host = None
        self.server_udp_port = None
        self.server_tcp_port = None
        self.stop_event = threading.Event()

    def run(self):
        self._startup_phase()

        while not self.stop_event.is_set():
            if self.state == ClientState.LOOKING_FOR_SERVER:
                self._listen_for_offers()
            elif self.state == ClientState.SPEED_TEST:
                self._perform_speed_test()
                # After finishing transfers, go back to looking for servers
                self.state = ClientState.LOOKING_FOR_SERVER
            time.sleep(0.2)

    def _startup_phase(self):
        """
        The client asks the user for the file size, the amount of TCP connections,
        and the amount of UDP connections.
        """
        # Ask user for the file size in bytes
        fs_str = input("Enter file size in bytes (e.g. 1000000000 for ~1GB): ")
        if fs_str.strip():
            try:
                self.file_size = int(fs_str)
            except ValueError:
                pass  # fallback to default

        # Ask user for the number of TCP connections
        tcp_str = input("Enter number of TCP connections (e.g. 1): ")
        if tcp_str.strip():
            try:
                self.num_tcp = int(tcp_str)
            except ValueError:
                pass  # fallback to default

        # Ask user for the number of UDP connections
        udp_str = input("Enter number of UDP connections (e.g. 2): ")
        if udp_str.strip():
            try:
                self.num_udp = int(udp_str)
            except ValueError:
                pass  # fallback to default

        print("Client started, listening for offer requests...")

        self.state = ClientState.LOOKING_FOR_SERVER

    def _listen_for_offers(self):
        """
        The client waits for an OfferMessage (UDP broadcast).
        Upon receiving one, transitions to SPEED_TEST.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("", DEFAULT_UDP_PORT))
        sock.settimeout(3.0)

        try:
            data, addr = sock.recvfrom(4096)
            offer = OfferMessage.decode(data)
            print(f"Received offer from {addr[0]}")
            self.server_host = addr[0]
            self.server_udp_port = offer.server_udp_port
            self.server_tcp_port = offer.server_tcp_port

            self.state = ClientState.SPEED_TEST
        except socket.timeout:
            pass
        except ValueError:
            pass
        finally:
            sock.close()

    def _perform_speed_test(self):
        """
        Connect over TCP and send file_size + '\n'.
        Also send a RequestMessage over UDP with file_size.
        All requests are in parallel with threads.
        """

        # Create threads for TCP downloads
        tcp_threads = []
        for i in range(self.num_tcp):
            t = threading.Thread(target=self._tcp_download_thread, args=(i + 1,))
            t.start()
            tcp_threads.append(t)

        # Create threads for UDP downloads
        udp_threads = []
        for i in range(self.num_udp):
            t = threading.Thread(target=self._udp_download_thread, args=(i + 1,))
            t.start()
            udp_threads.append(t)

        # Wait for them to finish
        for t in tcp_threads:
            t.join()
        for t in udp_threads:
            t.join()

        print("All transfers complete, listening to offer requests")

    def _tcp_download_thread(self, idx):
        """
        Sends the file_size via TCP, receives that many bytes, measures time & speed.
        Then prints out:
         “TCP transfer #<idx> finished, total time: x.xx seconds, total speed: y.yy bits/second”
        """
        start_time = time.time()
        received_bytes = 0

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.server_host, self.server_tcp_port))
            req_str = f"{self.file_size}\n".encode()
            s.sendall(req_str)

            while received_bytes < self.file_size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                received_bytes += len(chunk)
        except:
            # Ignore errors for simplicity
            pass
        finally:
            s.close()

        elapsed = time.time() - start_time
        # Convert bytes/second to bits/second => multiply by 8
        if elapsed > 0:
            speed_bits_per_sec = (received_bytes * 8) / elapsed
        else:
            speed_bits_per_sec = 0.0

        print(f"TCP transfer #{idx} finished, total time: {elapsed:.2f} seconds, "
              f"total speed: {speed_bits_per_sec:.2f} bits/second")

    def _udp_download_thread(self, idx):
        """
        Sends a RequestMessage over UDP, receives multiple PayloadMessages,
        measures total time & speed. Then prints:
         “UDP transfer #<idx> finished, total time: x.xx seconds,
          total speed: y.yy bits/second, percentage of packets received successfully: Z%”
        """
        start_time = time.time()

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)  # The scenario says the client detects the transfer after 1 second of no data

        # Send the request
        req_msg = RequestMessage(self.file_size)
        sock.sendto(req_msg.encode(), (self.server_host, self.server_udp_port))

        received_bytes = 0
        total_segments_expected = None
        segments_received = 0

        # Keep receiving until no data for 1s
        while True:
            try:
                data, addr = sock.recvfrom(65535)
                pm = PayloadMessage.decode(data)

                if total_segments_expected is None:
                    total_segments_expected = pm.total_segments

                received_bytes += len(pm.payload)
                segments_received += 1
                # We keep receiving until a timeout triggers => no more data
            except socket.timeout:
                # 1 second of no data => transfer done
                break
            except:
                # Ignore all other errors/invalid packets
                pass

        sock.close()
        elapsed = time.time() - start_time

        # Speed in bits/second
        if elapsed > 0:
            speed_bits_per_sec = (received_bytes * 8) / elapsed
        else:
            speed_bits_per_sec = 0.0

        # Packet loss or percentage of packets received:
        percent_received = 100.0
        if total_segments_expected is not None and total_segments_expected > 0:
            percent_received = 100.0 * segments_received / total_segments_expected

        print(f"UDP transfer #{idx} finished, total time: {elapsed:.2f} seconds, "
              f"total speed: {speed_bits_per_sec:.2f} bits/second, "
              f"percentage of packets received successfully: {percent_received:.0f}%")


if __name__ == "__main__":
    client = Client()
    try:
        client.run()
    except KeyboardInterrupt:
        # No extra prints required by scenario
        pass
