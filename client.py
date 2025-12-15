import socket
import struct

packer = struct.Struct("3s i i i")

with socket.socket() as client:
    client.connect(("localhost", 10001))

    cmd1 = packer.pack("SET".encode(), 1, 1, 5)
    cmd2 = packer.pack("SET".encode(), 1, 2, 10)
    cmd3 = packer.pack("SET".encode(), 2, 1, 5)
    cmd4 = packer.pack("GET".encode(), 1, 1, 5)
    cmd5 = packer.pack("SUM".encode(), 1, 1, 5)

    cmds = [cmd1, cmd2, cmd3, cmd4, cmd5]
    while True:
        name = input("enter name: ")
        diff = input("Enter num: ")
        
        for i in cmds:
            client.sendall(i)
            resp = struct.unpack("i", client.recv(struct.calcsize("i")))
            print(resp)

        data = packer.pack("SET".encode(), 2, 2, int(diff))
        client.sendall(data)
        resp = struct.unpack("i", client.recv(struct.calcsize("i")))
        print(resp)

        client.sendall(cmd5)
        resp = struct.unpack("i", client.recv(struct.calcsize("i")))
        print(resp)
        

