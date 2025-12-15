import socket
import sys
import struct

packer = struct.Struct("6s 13s 6s")

hostname = sys.argv[1]
port = int(sys.argv[2])

with socket.socket() as client:

    client.connect((hostname, port))
    packet = packer.pack(b"ckn7r8", b"9786156702340", b"submit")
    client.sendall(packet)

    days = 20

    available, d = struct.unpack("i i", client.recv(4096))
    
    if not available:
        packet = packer.pack(b"ckn7r8", b"9786156702340", b"cancel")
        client.sendall(packet)
    else:
        if d >= days:
            packet = packer.pack(b"ckn7r8", b"9786156702340", b"borrow")
            client.sendall(packet)
        else:
            packet = packer.pack(b"ckn7r8", b"9786156702340", b"extend")
            client.sendall(packet)
            status, t = struct.unpack("i i", client.recv(4096))
            if status and t >= 20:
                packet = packer.pack(b"ckn7r8", b"9786156702340", b"borrow")
                client.sendall(packet)
            else:
                packet = packer.pack(b"ckn7r8", b"9786156702340", b"cancel")
                client.sendall(packet)
            

    data = struct.unpack("12s", client.recv(4096))[0]
    print(data.decode())









