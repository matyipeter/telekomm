# Network Programming Exam Cheat Sheet

## 0. IMPORTS & TOOLS
```python
import socket
import struct
import select
import sys
import random
import json
import time

# --- COMMON CONFIG ---
# "4s i" = 4-char string + integer (e.g., "INCR", 5)
# "20s i" = 20-char string + integer
# "i" = just an integer (4 bytes)
PACKER_CMD = struct.Struct("4s i") 
PACKER_DATA = struct.Struct("20s i")
```

---

## 1. UNIVERSAL TCP CLIENT
*Uncomment the `get_input` section you need (A, B, or C).*

```python
import socket
import struct
import random
import json

SERVER_ADDR = ("localhost", 10000)
PACKER = struct.Struct("20s i") # CHECK EXAM REQUIREMENT!

def get_data():
    # --- VARIANT A: User + Random ---
    # txt = input("Text: ")
    # num = random.randint(1, 100)
    # return txt, num

    # --- VARIANT B: Read .txt File ---
    # # Format: "almafa 4" on each line
    # with open("input.txt", "r") as f:
    #     lines = f.readlines()
    # target = lines[random.randint(0, len(lines)-1)].strip().split()
    # return target[0], int(target[1])

    # --- VARIANT C: Read .json File ---
    # # Format: {"1": ["almafa", 4]}
    # with open("input.json", "r") as f:
    #     data = json.load(f)
    # key = str(random.randint(1, 3))
    # return data[key][0], data[key][1]
    
    return "default", 0

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(SERVER_ADDR)
        
        # 1. Prepare
        txt, num = get_data()
        print(f"Sending: {txt}, {num}")
        
        # 2. Pack & Send
        payload = PACKER.pack(txt.encode(), num)
        client.sendall(payload)
        
        # 3. Receive
        data = client.recv(1024)
        
        # IF RESPONSE IS STRING:
        print(f"Server replied: {data.decode()}")
        
        # IF RESPONSE IS STRUCT (e.g. integer):
        # res = struct.unpack("i", data)[0]
        # print(f"Server value: {res}")

if __name__ == "__main__":
    main()
```

---

## 2. TCP SERVER (SELECT / MULTIPLEX)
*Handles IN, INCR, DECR commands.*

```python
import socket
import select
import struct

SERVER_ADDR = ("localhost", 10000)
PACKER = struct.Struct("4s i") # IN, INCR, DECR

def main():
    val = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setblocking(False)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(SERVER_ADDR)
        server.listen(5)
        
        inputs = [server]
        print(f"Listening on {SERVER_ADDR}...")
        
        while inputs:
            try:
                readable, _, exceptional = select.select(inputs, [], inputs, 1)
                
                for sock in readable:
                    if sock is server:
                        c, _ = server.accept()
                        c.setblocking(False)
                        inputs.append(c)
                    else:
                        data = sock.recv(1024)
                        if data:
                            cmd_raw, x = PACKER.unpack(data)
                            cmd = cmd_raw.decode().strip('\x00')
                            
                            if cmd == "IN": val = x
                            elif cmd == "INCR": val += x
                            elif cmd == "DECR": val -= x
                            
                            # Reply: check if they want BYTES or STRUCT
                            sock.sendall(str(val).encode()) 
                        else:
                            inputs.remove(sock)
                            sock.close()
                            
                for sock in exceptional:
                    inputs.remove(sock)
                    sock.close()
                    
            except KeyboardInterrupt:
                for s in inputs: s.close()
                inputs = []

if __name__ == "__main__":
    main()
```

---

## 3. PROXY SERVER (TCP -> UDP)
*Forwards TCP requests to a UDP server and returns the answer.*

```python
import socket
import select

TCP_PORT = 10000
UDP_ADDR = ("localhost", 11000)

def main():
    udp_cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
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
                        c, _ = proxy.accept()
                        c.setblocking(False)
                        inputs.append(c)
                    else:
                        data = sock.recv(1024)
                        if data:
                            # 1. Forward to UDP
                            udp_cli.sendto(data, UDP_ADDR)
                            # 2. Get Reply
                            reply, _ = udp_cli.recvfrom(1024)
                            # 3. Send back to TCP Client
                            sock.sendall(reply)
                        else:
                            inputs.remove(sock)
                            sock.close()
            except KeyboardInterrupt:
                break
if __name__ == "__main__":
    main()
```

---

## 4. UDP SERVER (Basic or Buggy)
*Use for the backend storage.*

```python
import socket
import struct
import random

ADDR = ("localhost", 11000)
PACKER = struct.Struct("5s i") # PUSH, PLUS, MINUS

def main():
    val = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(ADDR)
        print("UDP Ready...")
        while True:
            data, cli_addr = server.recvfrom(1024)
            cmd_raw, x = PACKER.unpack(data)
            cmd = cmd_raw.decode().strip('\x00')
            
            # BUGGY LOGIC:
            # x += random.randint(-1, 1)
            
            if cmd == "PUSH": val = x
            elif cmd == "PLUS": val += x
            elif cmd == "MINUS": val -= x
            
            # Reply as struct
            server.sendto(struct.pack("i", val), cli_addr)

if __name__ == "__main__":
    main()
```

## 5. FILE GENERATORS (Run once)

```python
# input.txt
with open("input.txt", "w") as f:
    f.write("almafa 4\nkortefa 3\nbarackfa 5\n")

# input.json
import json
d = {"1": ["almafa", 4], "2": ["kortefa", 3], "3": ["barackfa", 5]}
with open("input.json", "w") as f:
    json.dump(d, f)
```
