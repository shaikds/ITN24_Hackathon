# Network Speed Test Application

## Description
This Python-based client-server application performs network speed tests, comparing UDP and TCP downloads to evaluate network performance under various conditions.

## Features
- **Client-Server Architecture**: Implements both UDP and TCP protocols to assess network speeds.
- **Concurrency Handling**: Manages multiple network connections simultaneously using threading.
- **Dynamic Configuration**: Allows users to specify the file size and the number of TCP and UDP connections dynamically.

## Getting Started

### Prerequisites
- Python 3.x
- Scapy

### Installation
1. **Clone the Repository**
   Clone the project to your local machine:
   ```bash
   git clone https://github.com/shaikds/network-speed-test.git
### Install Dependencies
Install the required Python packages:

pip install scapy

### Running the Application
Server
To start the server, execute the following command from the root directory of the project:

python server.py

The server will print its IP address and start sending UDP offers.

### Client
To run the client, execute:

python client.py

Follow the on-screen instructions to set download parameters.

## Usage Example
### Start the Server:
It will display its IP address and begin broadcasting UDP offers.
### Start the Client:
Enter the requested file size and the number of TCP and UDP connections.
Once an offer is received, the client connects to the server to start the speed tests.
