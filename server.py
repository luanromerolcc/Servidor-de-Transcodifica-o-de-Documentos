import socket
import threading
import logging
from converters import CONVERTERS


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

HOST = "0.0.0.0"
PORT = 9000
MAX_PARALLEL = 4
CHUNK_SIZE = 1024

semaphore = threading.Semaphore(MAX_PARALLEL)
sessions = {}
sessions_lock = threading.Lock()

def handle_conversion(addr, session):
    key = f"{session['fin']}:{session['fout']}"
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as thread_sock:
        thread_sock.settimeout(0.5) # Timeout de retransmissão

        if key not in CONVERTERS:
            thread_sock.sendto(f"ERR:formato '{key}' nao suportado\n".encode(), addr)
            logging.warning(f"Formato invalido solicitado por {addr}: {key}")
            return

        with semaphore:
            try:
                chunks = [session['chunks'][i] for i in sorted(session['chunks'])]
                data = b"".join(chunks)
                
                logging.info(f"Iniciando conversao para {addr} ({key})")
                result = CONVERTERS[key](data.decode("utf-8"))
                result_bytes = result.encode("utf-8")
                
                # Avisa o tamanho total (usando o novo socket)
                thread_sock.sendto(f"OK:{len(result_bytes)}\n".encode(), addr)
                
                # Envio Fragmentado com Stop-and-Wait
                seq = 0
                offset = 0
                while offset < len(result_bytes):
                    chunk = result_bytes[offset:offset + CHUNK_SIZE]
                    packet = b"DAT:" + str(seq).encode() + b":" + str(len(chunk)).encode() + b":" + chunk
                    
                    ack_received = False
                    while not ack_received:
                        thread_sock.sendto(packet, addr)
                        try:
                            # Escuta o ACK na porta exclusiva desta thread
                            ack_packet, _ = thread_sock.recvfrom(1024)
                            if ack_packet.decode().strip() == f"ACK:{seq}":
                                ack_received = True
                        except socket.timeout:
                            logging.warning(f"[Timeout] Pacote {seq} para {addr} perdido. Retransmitindo...")
                    
                    offset += len(chunk)
                    seq += 1
                    
                logging.info(f"Conversao finalizada e enviada para {addr}")

            except Exception as e:
                logging.error(f"Erro ao processar conversao de {addr}: {e}")
                thread_sock.sendto(b"ERR:Erro interno na conversao\n", addr)


HOST_PORT = (HOST, PORT)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
    server_sock.bind(HOST_PORT)
    logging.info(f"Servidor UDP rodando em {HOST}:{PORT}")
    
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
            try:
                header, payload = packet.split(b":", 3)[1:4], packet.split(b":", 3)[3]
                seq = int(header[0])
                length = int(header[1])
            except Exception:
                continue # ignora pacote malformado se houver erro no split
                
            with sessions_lock:
                session = sessions.get(addr)
            if not session:
                continue
            if seq not in session["chunks"]:
                session["chunks"][seq] = payload
                session["received"] += len(payload)
            
            # O servidor confirma o pacote que o cliente enviou
            server_sock.sendto(f"ACK:{seq}\n".encode(), addr)
            
            if session["received"] >= session["size"]:
                with sessions_lock:
                    sessions.pop(addr, None)
                # Removido o server_sock dos argumentos da thread
                thread = threading.Thread(target=handle_conversion, args=(addr, session))
                thread.daemon = True
                thread.start()