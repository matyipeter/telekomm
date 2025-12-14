# Python Network Programming Master Cheat Sheet

## 0. IMPORTS
```python
import socket
import select
import struct
import sys
import random
import json
import time
```

---

## 1. TCP BOILERPLATE (Reliable, Stream)

### TCP Server
```python
# SERVER_ADDR = ("localhost", 10000)
def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("localhost", 10000))
        server.listen(5)
        print("TCP Server Waiting...")
        
        while True:
            # Blocks until a client connects
            conn, addr = server.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024)
                if not data: break
                
                # Process & Send Back
                conn.sendall(data) 
```

### TCP Client
```python
def tcp_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(("localhost", 10000))
        
        # Send
        client.sendall(b"Hello TCP")
        
        # Receive
        data = client.recv(1024)
        print(f"Received: {data.decode()}")
```

---

## 2. UDP BOILERPLATE (Unreliable, Packets)

### UDP Server
```python
def udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.bind(("localhost", 11000))
        print("UDP Server Waiting...")
        
        while True:
            # Receive data + address
            data, addr = server.recvfrom(1024)
            print(f"Msg from {addr}: {data}")
            
            # Send back to specific address
            server.sendto(b"ACK", addr)
```

### UDP Client
```python
def udp_client():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        server_addr = ("localhost", 11000)
        
        # Send (Must specify address)
        client.sendto(b"Hello UDP", server_addr)
        
        # Receive
        data, _ = client.recvfrom(1024)
        print(f"Received: {data}")
```

---

## 3. STRUCT (Binary Packing)
*Format: `i`=int(4), `f`=float, `10s`=string(10 bytes)*

```python
import struct

# DEFINE: "10s i" -> 10-byte string + integer
packer = struct.Struct("10s i") 

def send_struct(sock):
    text = "Player1"
    score = 500
    # Pack: Encode string! Auto-pads with nulls.
    payload = packer.pack(text.encode(), score)
    sock.sendall(payload)

def recv_struct(sock):
    data = sock.recv(1024) # or packer.size
    try:
        # Unpack returns tuple
        raw_txt, score = packer.unpack(data)
        
        # Clean string: decode and strip null bytes
        clean_txt = raw_txt.decode().strip('\x00')
        print(f"User: {clean_txt}, Score: {score}")
    except:
        print("Struct Error")
```

---

## 4. SELECT (Multiplexing TCP Server)
*Handle multiple clients at once.*

```python
def select_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(False) # CRITICAL
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", 10000))
    server.listen(5)
    
    inputs = [server] # Watch list
    
    while inputs:
        try:
            # 1. Wait for events (Read, Write, Exception, Timeout)
            readable, _, exceptional = select.select(inputs, [], inputs, 1)
            
            for sock in readable:
                if sock is server:
                    # NEW CONNECTION
                    c, addr = server.accept()
                    c.setblocking(False)
                    inputs.append(c)
                else:
                    # EXISTING CLIENT DATA
                    data = sock.recv(1024)
                    if data:
                        # Logic here (e.g., Struct unpack)
                        sock.sendall(data)
                    else:
                        # DISCONNECT
                        inputs.remove(sock)
                        sock.close()
                        
            # Handle Errors
            for sock in exceptional:
                inputs.remove(sock)
                sock.close()
                
        except KeyboardInterrupt:
            break
```

---

## 5. PROXY PATTERN (TCP Frontend -> UDP Backend)
*Place this logic INSIDE the `else` block of the Select Server above.*

```python
# SETUP (Before loop)
udp_backend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
BACKEND_ADDR = ("localhost", 11000)

# INSIDE LOOP (When 'sock' has data):
    data = sock.recv(1024)
    if data:
        # 1. Forward TCP data to UDP Server
        udp_backend.sendto(data, BACKEND_ADDR)
        
        # 2. Wait for UDP Reply
        reply, _ = udp_backend.recvfrom(1024)
        
        # 3. Send UDP Reply back to TCP Client
        sock.sendall(reply)
```

---

## 6. FILE READING HELPERS

```python
def read_txt_line():
    # File format: "almafa 4"
    with open("input.txt", "r") as f:
        lines = f.readlines()
        line = lines[random.randint(0, len(lines)-1)]
        parts = line.strip().split()
        return parts[0], int(parts[1])

def read_json_key():
    # File format: {"1": ["almafa", 4]}
    with open("input.json", "r") as f:
        data = json.load(f)
        key = str(random.randint(1, len(data)))
        return data[key][0], data[key][1]
```
