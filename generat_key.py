from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import ipaddress

# Generate private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
CNT = "US" # Country code for certificate subject like "US" (str)
SERVER_IP =  #your_ip_here  (str)     
# Certificate subject (str)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, CNT),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TLS-Test"),
    x509.NameAttribute(NameOID.COMMON_NAME, SERVER_IP),
])

# Certificate with SAN (IP)
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365*100))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address(SERVER_IP))
        ]),
        critical=False
    )
    .sign(key, hashes.SHA256())
)

# Write key
with open("server.key", "wb") as f:
    f.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# Write certificate
with open("server.crt", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("✔️ server.crt و server.key  ok")