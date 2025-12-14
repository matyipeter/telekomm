Python Network Programming Exam Cheat Sheet
0. Quick Reference & Imports
Standard Imports:

Python

import socket
import struct
import select
import sys
import random
import json
import time
Struct Formats:

i = integer (4 bytes)

4s = string of 4 bytes (char array)

20s = string of 20 bytes

Packing: packer.pack(text.encode(), number) (Auto-pads with \x00)

Unpacking: txt_bytes, num = packer.unpack(data) -> txt = txt_bytes.decode().strip('\x00')

1. TCP Client (The "Chameleon")
Use this base for ALL client tasks. Swap the Input Block based on the task.

Python

import socket
import struct
import random
import json

# --- CONFIG ---
SERVER_ADDR = ("localhost", 10000)
# UPDATE THIS FORMAT BASED ON TASK! (e.g., "20s i" or "4s i")
PACKER = struct.Struct("20s i") 

def get_input_data():
    """ 
    SWAP THIS FUNCTION CONTENT BASED ON TASK A, B, or C 
    Must return tuple: (text_string, integer)
    """
    # --- VARIANT A: User Input ---
    # txt = input("Text: ")
    # num = random.randint(1, 100)
    # return txt, num

    # --- VARIANT B: .txt File ---
    # target_line = random.randint(1, 3)
    # with open("input.txt", "r") as f:
    #     lines = f.readlines()
    #     # File format: "almafa 4"
    #     line = lines[target_line - 1].strip().split() 
    #     return line[0], int(line[1])

    # --- VARIANT C: .json File ---
    # key = str(random.randint(1, 3))
    # with open("input.json", "r") as f:
    #     data = json.load(f)
    #     # Format: {"1": ["almafa", 4]}
    #     return data[key][0], data[key][1]
    
    return "default", 0

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(SERVER_ADDR)
        
        # 1. Prepare Data
        text, number = get_input_data()
        print(f"Sending: {text}, {number}")
        
        # 2. Pack & Send
        # .encode() is crucial. struct pads automatically for 's'.
        payload = PACKER.pack(text.encode(), number) 
        client.sendall(payload)
        
        # 3. Receive Response
        # Adjust buffer size or unpack format based on server response!
        data = client.recv(1024)
        
        # IF Server sends struct back (e.g. just an int 'i'):
        # res = struct.unpack("i", data)[0]
        # print(f"Received int: {res}")
        
        # IF Server sends string back (e.g. "Xs"):
        # res = data.decode()
        # print(f"Received str: {res}")

if __name__ == "__main__":
    main()
1.1 UDP Client Variant
If task asks for UDP Client, change main to this:

Python

def main_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        text, number = get_input_data()
        payload = PACKER.pack(text.encode(), number)
        
        # UDP uses sendto and recvfrom
        client.sendto(payload, SERVER_ADDR)
        
        data, addr = client.recvfrom(1024)
        print(f"Received: {data}") # Decode or Unpack as needed
2. TCP Server (Multiplexing / Select)
Handles multiple clients, keeps state (num), processes commands.

Python

import socket
import select
import struct

SERVER_ADDR = ("localhost", 10000)
PACKER = struct.Struct("4s i") # e.g., IN, INCR, DECR

def main():
    server_state = 0 # The integer we are storing
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setblocking(False)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(SERVER_ADDR)
        server.listen(5)
        
        inputs = [server]
        print(f"TCP Server listening on {SERVER_ADDR}")
        
        while inputs:
            try:
                readable, _, exceptional = select.select(inputs, [], inputs, 1)
                
                for sock in readable:
                    if sock is server:
                        conn, addr = server.accept()
                        conn.setblocking(False)
                        inputs.append(conn)
                    else:
                        data = sock.recv(1024)
                        if data:
                            # --- LOGIC START ---
                            cmd_bytes, val = PACKER.unpack(data)
                            cmd = cmd_bytes.decode().strip('\x00') # Clean nulls
                            
                            print(f"Cmd: {cmd}, Val: {val}")
                            
                            if cmd == "IN":
                                server_state = val
                            elif cmd == "INCR":
                                server_state += val
                            elif cmd == "DECR":
                                server_state -= val
                                
                            # Send back current state as BYTES (str) or STRUCT
                            # Task says "bytesztringként" (as bytestring) usually:
                            sock.sendall(str(server_state).encode())
                            
                            # If task says struct response:
                            # sock.sendall(struct.pack("i", server_state))
                            # --- LOGIC END ---
                        else:
                            inputs.remove(sock)
                            sock.close()
                            
                for sock in exceptional:
                    inputs.remove(sock)
                    sock.close()
                    
            except KeyboardInterrupt:
                for s in inputs: s.close()
                inputs = []
                break

if __name__ == "__main__":
    main()
3. Proxy Server (TCP Frontend -> UDP Backend)
The "Complex" task. Receives TCP command, forwards to UDP server, gets reply, sends back to TCP client.

Python

import socket
import select
import struct

TCP_PORT = 10000  # Proxy listens here
UDP_ADDR = ("localhost", 11000) # Real UDP server is here

def main():
    # UDP Client Socket (to talk to backend)
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # TCP Server Socket (to talk to users)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy:
        proxy.setblocking(False)
        proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy.bind(("localhost", TCP_PORT))
        proxy.listen(5)
        
        inputs = [proxy]
        
        while inputs:
            try:
                readable, _, _ = select.select(inputs, [], [], 1)
                for sock in readable:
                    if sock is proxy:
                        c, a = proxy.accept()
                        c.setblocking(False)
                        inputs.append(c)
                    else:
                        data = sock.recv(1024)
                        if data:
                            print("Forwarding to UDP...")
                            # 1. Send raw data to UDP Server
                            udp_client.sendto(data, UDP_ADDR)
                            
                            # 2. Wait for UDP reply
                            # Note: In strict async, this blocks, but usually ok for this exam level
                            resp, _ = udp_client.recvfrom(1024)
                            
                            # 3. Forward reply back to TCP Client
                            sock.sendall(resp)
                        else:
                            inputs.remove(sock)
                            sock.close()
            except KeyboardInterrupt:
                break
4. UDP Server (With "Buggy" Logic)
The backend server for the proxy task.

Python

import socket
import struct
import random

ADDR = ("localhost", 11000)
PACKER = struct.Struct("5s i") # PUSH, PLUS, MINUS

def main():
    server_val = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(ADDR)
        print(f"UDP Server on {ADDR}")
        
        while True:
            data, client_addr = server.recvfrom(1024)
            
            cmd_bytes, val = PACKER.unpack(data)
            cmd = cmd_bytes.decode().strip('\x00')
            
            # --- BUGGY LOGIC (If requested) ---
            error = random.randint(-1, 1) 
            # val += error # Uncomment to make it buggy
            
            if cmd == "PUSH":
                server_val = val
            elif cmd == "PLUS":
                server_val += val
            elif cmd == "MINUS":
                server_val -= val
                
            print(f"State: {server_val}")
            
            # Response in Struct "i"
            resp = struct.pack("i", server_val)
            server.sendto(resp, client_addr)

if __name__ == "__main__":
    main()
5. File Helpers (Copy-Paste if needed)
Create input.txt:

Python

with open("input.txt", "w") as f:
    f.write("almafa 4\n")
    f.write("kortefa 3\n")
    f.write("barackfa 5\n")
Create input.json:

Python

import json
data = {
    "1": ["almafa", 4],
    "2": ["kortefa", 3],
    "3": ["barackfa", 5]
}
with open("input.json", "w") as f:
    json.dump(data, f)
