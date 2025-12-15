# Network Data Handling & Struct Serialization Guide

## 1. The Core Philosophy
**The Hard Truth:** TCP is a **stream**, not a message queue. 
There are no "packets" once the data hits the OS buffer; there is only a continuous river of bytes. 

* **Sender:** Must serialize data into a strict binary format.
* **Receiver:** Must know *exactly* how many bytes to pull from the stream to reconstruct the message.

---

## 2. The Golden Rule of `struct`
**Never rely on native byte alignment for network traffic.**
Different machines (and OSs) handle memory alignment differently. A C-struct on Linux might be 16 bytes, while on Windows it's 24 bytes due to padding.

* **Bad:** `struct.Struct('i 20s')` (Uses native alignment/padding. Unpredictable.)
* **Good:** `struct.Struct('!i 20s')` (The `!` forces **Network Byte Order** (Big-Endian) and standard sizes. No padding.)

---

## 3. Client Side: Packing Data
The client's job is to convert Python types (`int`, `str`) into a `bytes` object.

### The Code
```python
import struct
import socket

# Define format: 
# '!' = Network (Big-Endian)
# 'i' = integer (4 bytes)
# '20s' = string of 20 chars (20 bytes)
# Total Size: 24 bytes
PACKER = struct.Struct('!i20s')

def send_request(sock, urgency, message):
    # 1. Encode string to bytes
    msg_bytes = message.encode('utf-8')
    
    # 2. Pack the data
    # Note: struct.pack requires the string to be bytes. 
    # '20s' will pad with null bytes if the string is shorter than 20.
    payload = PACKER.pack(urgency, msg_bytes)
    
    # 3. Send ALL bytes
    sock.sendall(payload)
```

## Server side data recieving

```python
def recvall(sock, num_bytes):
    """
    Guarantees returning exactly 'num_bytes' or None if connection closes.
    Blocks until data is available.
    """
    data = b''
    while len(data) < num_bytes:
        try:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None # Connection closed
            data += chunk
        except socket.error:
            return None
    return data

# Usage Implementation
raw_data = recvall(client_sock, PACKER.size)
if raw_data:
    urgency, msg_bytes = PACKER.unpack(raw_data)
    # Decode and strip null padding
    message = msg_bytes.decode('utf-8').strip('\x00')
```

## Buffered reading
```python
def handle_stream(sock):
    buff = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk: break
        buff += chunk
        
        # Process loop: Do we have enough data for a full message?
        while len(buff) >= PACKER.size:
            # 1. Slice out the message
            message_data = buff[:PACKER.size]
            
            # 2. Keep the rest for the next iteration
            buff = buff[PACKER.size:]
            
            # 3. Unpack and Execute
            urgency, msg_bytes = PACKER.unpack(message_data)
            print(f"Processed: {urgency}")
```

