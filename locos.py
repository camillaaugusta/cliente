import socket
import select

class ChatServer:
    def __init__(self, host='192.168.1.2', port=2222):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}  # {socket: username}
        self.private_chats = {}  # {socket: target_username}
        print(f"Servidor rodando em {host}:{port}")
        print("Comandos disponíveis:")
        print("/p usuario - inicia chat privado")
        print("/sair - sai do chat privado")

    def broadcast(self, message, sender=None):
        """Envia uma mensagem para todos os clientes, exceto o remetente."""
        for client in list(self.clients):  # Usando list para evitar erros ao iterar lembrar arthur
            if client != sender:
                try:
                    client.send(message.encode())
                except:
                    self.remove_client(client)

    def send_private(self, sender, target_username, message):
        """Envia uma mensagem privada para um cliente."""
        for client, username in self.clients.items():
            if username == target_username:
                try:
                    client.send(f"[Privado de {self.clients[sender]}] {message}".encode())
                    sender.send(f"[Privado para {target_username}] {message}".encode())
                    return True
                except:
                    self.remove_client(client)
        return False

    def remove_client(self, client):
        """Remove um cliente do chat."""
        if client in self.clients:
            username = self.clients[client]
            del self.clients[client]
            if client in self.private_chats:
                del self.private_chats[client]
            try:
                client.close()
            except Exception as e:
                print(f"Erro ao fechar o cliente {username}: {e}")
            self.broadcast(f"{username} saiu do chat!")

    def process_command(self, client, message):
        """Processa comandos enviados por um cliente."""
        if message.startswith('/p '):
            try:
                target = message.split()[1]
                if target in [username for username in self.clients.values()]:
                    self.private_chats[client] = target
                    client.send(f"Iniciando chat privado com {target}".encode())
                else:
                    client.send("Usuário não encontrado.".encode())
            except IndexError:
                client.send("Uso: /p usuario".encode())
        elif message == '/sair':
            if client in self.private_chats:
                target = self.private_chats[client]
                del self.private_chats[client]
                client.send(f"Saiu do chat privado com {target}".encode())
            else:
                client.send("Você não está em um chat privado.".encode())
        else:
            return False
        return True

    def run(self):
        """Executa o servidor."""
        while True:
            try:
                readable, _, _ = select.select([self.server] + list(self.clients.keys()), [], [], 0.1)
                for sock in readable:
                    if sock == self.server:
                        client, addr = self.server.accept()
                        username = client.recv(1024).decode().strip()
                        self.clients[client] = username
                        print(f"Novo cliente: {username}")
                        self.broadcast(f"{username} entrou no chat!")
                        client.send("Comandos: /p usuario (chat privado), /sair (sair do privado)".encode())
                    else:
                        try:
                            message = sock.recv(1024).decode().strip()
                            if message:
                                if message.startswith('/'):
                                    self.process_command(sock, message)
                                else:
                                    if sock in self.private_chats:
                                        target = self.private_chats[sock]
                                        if not self.send_private(sock, target, message):
                                            sock.send("Usuário não está mais online.".encode())
                                            del self.private_chats[sock]
                                    else:
                                        self.broadcast(f"{self.clients[sock]}: {message}", sock)
                            else:
                                self.remove_client(sock)
                        except:
                            self.remove_client(sock)
            except Exception as e:
                print(f"Erro no servidor: {str(e)}")

if __name__ == "__main__":
    server = ChatServer()
    server.run()
