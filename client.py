import socket
import sys

HOST = "127.0.0.1"
PORT = 9000

def send_file(path, fin, fout):
    with open(path, "rb") as f:
        data = f.read()
    with socket.create_connection((HOST, PORT)) as conn:
        header = f"{fin}:{fout}:{len(data)}\n".encode()
        conn.sendall(header)
        conn.sendall(data)
        response_header = b""
        while not response_header.endswith(b"\n"):
            response_header += conn.recv(1)
        status, *rest = response_header.decode().strip().split(":")
        if status == "ERR":
            print("Erro:", ":".join(rest))
            return
        size = int(rest[0])
        result = b""
        while len(result) < size:
            chunk = conn.recv(min(4096, size - len(result)))
            if not chunk:
                break
            result += chunk

    print(result.decode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python client.py <arquivo> <format_in> <format_out>")
        print("Exemplo: python client.py README.md md html")
        sys.exit(1)

    send_file(sys.argv[1], sys.argv[2], sys.argv[3])
