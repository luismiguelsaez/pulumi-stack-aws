import ssl
import hashlib

def get_ssl_cert_fingerprint(host: str, port: int = 443):
    cert = ssl.get_server_certificate((host, port))
    der_cert = ssl.PEM_cert_to_DER_cert(cert)
    sha1 = hashlib.sha1(der_cert).hexdigest()

    return sha1
