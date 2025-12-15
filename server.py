import socket
import struct
import select
import sys


address = ("localhost", 10001)

matrix: list[list[int]] = [[0,0,0],[0,0,0],[0,0,0]]

packer = struct.Struct("3s i i i")

def sum_m(m):
    s = 0
    for i in m:
        s += sum(i)
    return s


with socket.socket() as server:
    server.setblocking(False) # CRITICAL
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(5)
    
    inputs = [server] # Watch list
    
    while inputs:
        try:
            # 1. Wait for events (Read, Write, Exception, Timeout)
            r, w, e = select.select(inputs, [], [], 1)
            
            for sock in r:
                if sock is server:
                    # NEW CONNECTION
                    c, addr = server.accept()
                    c.setblocking(False)
                    inputs.append(c)
                else:
                    data = sock.recv(packer.size)
                    if data:
                        cmd, r, c, v = packer.unpack(data)

                        match cmd.decode():
                            case "GET":
                                sock.sendall(struct.pack("i", matrix[r][c]))
                            case "SET":
                                matrix[r][c] = v
                                sock.sendall(struct.pack("i", matrix[r][c]))
                            case "SUM":
                                sock.sendall(struct.pack("i", sum_m(matrix)))
                    else:
                        # DISCONNECT
                        inputs.remove(sock)
                        sock.close()

        except KeyboardInterrupt:
            for sock in inputs:
                inputs.remove(sock)
                sock.close()
            inputs = []
                


