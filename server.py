import socket
import threading
from converters import CONVERTERS

HOST = "0.0.0.0"
PORT = 9000
MAX_PARALLEL = 4

semaphore = threading.Semaphore(MAX_PARALLEL)
sessions = {}
sessions_lock = threading.Lock()


def handle_conversion(addr, session, sock):
    key = f"{session['fin']}:{session['fout']}"
    if key not in CONVERTERS:
        sock.sendto(f"ERR:formato '{key}' nao suportado\n".encode(), addr)
        return

    with semaphore:
        chunks = [session['chunks'][i] for i in sorted(session['chunks'])]
        data = b"".join(chunks)
        result = CONVERTERS[key](data.decode("utf-8"))
        result_bytes = result.encode("utf-8")
        sock.sendto(f"OK:{len(result_bytes)}\n".encode(), addr)
        sock.sendto(result_bytes, addr)


HOST_PORT = (HOST, PORT)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
    server_sock.bind(HOST_PORT)
    while True:
        packet, addr = server_sock.recvfrom(65535)
        if packet.startswith(b"HDR:"):
            parts = packet.decode().strip().split(":")
            if len(parts) != 4:
                continue
            _, fin, fout, size = parts
            session = {
                "fin": fin,
                "fout": fout,
                "size": int(size),
                "received": 0,
                "chunks": {},
            }
            with sessions_lock:
                sessions[addr] = session
            server_sock.sendto(b"ACK:HDR\n", addr)

        elif packet.startswith(b"DAT:"):
            header, payload = packet.split(b":", 3)[1:4], packet.split(b":", 3)[3]
            seq = int(header[0])
            length = int(header[1])
            with sessions_lock:
                session = sessions.get(addr)
            if not session:
                continue
            if seq not in session["chunks"]:
                session["chunks"][seq] = payload
                session["received"] += len(payload)
            if session["received"] >= session["size"]:
                with sessions_lock:
                    sessions.pop(addr, None)
                thread = threading.Thread(target=handle_conversion, args=(addr, session, server_sock))
                thread.daemon = True
                thread.start()
