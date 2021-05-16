import socket
import json
import os

def get_speed(ip, port):
    try:
       sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       server_address = (ip, port)
       sock.settimeout(3)
       sock.connect(server_address)
    except:
        return 0

    try:
        request = {"id": 0, "jsonrpc": "2.0", "method": "miner_getstat1"}
        sock.sendall(json.dumps(request).encode())
        sock.sendall(os.linesep.encode())
        sock.shutdown(socket.SHUT_WR)  # no more writing
        with sock.makefile('r', encoding='utf-8') as file:
            response = json.load(file)
        json_answer = response.get('result')
        speed = json_answer[2].split(';')[0]
        return speed
    except:
        return 0
    finally:
        sock.close()

if __name__ == '__main__':
    speed = get_speed('11.11.0.16', 3333)
    print(speed)