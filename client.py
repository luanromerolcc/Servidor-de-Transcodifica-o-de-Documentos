import socket
import sys

HOST = "127.0.0.1"
PORT = 9000
CHUNK_SIZE = 1024


def send_file(path, fin, fout):
    with open(path, "rb") as f:
        data = f.read()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server_addr = (HOST, PORT)
        header = f"HDR:{fin}:{fout}:{len(data)}\n".encode()
        sock.sendto(header, server_addr)

        ack = b""
        while not ack.endswith(b"\n"):
            ack, _ = sock.recvfrom(4096)
            if ack.startswith(b"ACK:HDR"):
                break

        seq = 0
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + CHUNK_SIZE]
            packet = b"DAT:" + str(seq).encode() + b":" + str(len(chunk)).encode() + b":" + chunk
            sock.sendto(packet, server_addr)
            offset += len(chunk)
            seq += 1

        response_header = b""
        while not response_header.endswith(b"\n"):
            response_header, _ = sock.recvfrom(4096)
        status, *rest = response_header.decode().strip().split(":")
        if status == "ERR":
            print("Erro:", ":".join(rest))
            return

        size = int(rest[0])
        result = b""
        while len(result) < size:
            chunk, _ = sock.recvfrom(4096)
            result += chunk

    print(result.decode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python client.py <arquivo> <format_in> <format_out>")
        print("Exemplo: python client.py README.md md html")
        sys.exit(1)

    send_file(sys.argv[1], sys.argv[2], sys.argv[3])
