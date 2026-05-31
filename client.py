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
            
            # Lógica de Stop-and-Wait no Envio
            ack_received = False
            while not ack_received:
                sock.sendto(packet, server_addr)
                sock.settimeout(0.5)  # Espera meio segundo pelo ACK
                try:
                    ack_packet, _ = sock.recvfrom(1024)
                    if ack_packet.decode().strip() == f"ACK:{seq}":
                        ack_received = True
                except socket.timeout:
                    print(f"[!] Pacote {seq} perdido ou ACK atrasado. Retransmitindo...")
            
            offset += len(chunk)
            seq += 1
        
        # Configura um timeout de 5 segundos para não travar o cliente aguardando a conversão
        sock.settimeout(5.0)

        try:
            response_header = b""
            while not response_header.endswith(b"\n"):
                chunk, _ = sock.recvfrom(4096)
                response_header += chunk
                
            status, *rest = response_header.decode().strip().split(":")
            if status == "ERR":
                print("Erro do Servidor:", ":".join(rest))
                return

            size = int(rest[0])
            response_chunks = {} 
            received = 0
            
            while received < size:
                # Modificado para capturar também o endereço (recv_addr) da thread do servidor
                packet, recv_addr = sock.recvfrom(4096)
                
                if packet.startswith(b"DAT:"):
                    header, payload = packet.split(b":", 3)[1:4], packet.split(b":", 3)[3]
                    seq_recv = int(header[0]) # seq_recv para não confundir com o seq lá de cima
                    
                    # Envia o ACK de volta para a thread do servidor
                    sock.sendto(f"ACK:{seq_recv}\n".encode(), recv_addr)
                    
                    if seq_recv not in response_chunks:
                        response_chunks[seq_recv] = payload
                        received += len(payload)

            ordered_chunks = [response_chunks[i] for i in sorted(response_chunks)]
            result = b"".join(ordered_chunks)
            print(result.decode("utf-8"))

        except socket.timeout:
            print("Erro: O tempo limite da conexão foi excedido (Timeout). Pacotes foram perdidos.")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python client.py <arquivo> <format_in> <format_out>")
        print("Exemplo: python client.py README.md md html")
        sys.exit(1)

    send_file(sys.argv[1], sys.argv[2], sys.argv[3])