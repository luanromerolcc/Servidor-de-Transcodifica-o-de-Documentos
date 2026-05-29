import socketserver
import threading
from converters import CONVERTERS

HOST = "0.0.0.0"
PORT = 9000
MAX_PARALLEL = 4

semaphore = threading.Semaphore(MAX_PARALLEL)

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        header = b""
        while not header.endswith(b"\n"):
            header += conn.recv(1)
        format_in, format_out, size = header.decode().strip().split(":")
        size = int(size)
        data = b""
        while len(data) < size:
            chunk = conn.recv(min(4096, size - len(data)))
            if not chunk:
                break
            data += chunk

        key = f"{format_in}:{format_out}"
        if key not in CONVERTERS:
            conn.sendall(f"ERR:formato '{key}' nao suportado\n".encode())
            return
        with semaphore:
            result = CONVERTERS[key](data.decode("utf-8"))
        result_bytes = result.encode("utf-8")
        conn.sendall(f"OK:{len(result_bytes)}\n".encode())
        conn.sendall(result_bytes)

class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    with Server((HOST, PORT), Handler) as server:
        print(f"Servidor rodando em {HOST}:{PORT}")
        server.serve_forever()
