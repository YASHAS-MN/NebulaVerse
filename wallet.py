from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import binascii

class Wallet:
    def __init__(self):
        # 1. Generate a new Private/Public key pair for the user
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    @property
    def identity(self):
        """Returns the public key as a clean hex string (the User ID)"""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return binascii.hexlify(pub_bytes).decode('ascii')

    @property
    def public_key_pem(self):
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pub_bytes.decode("utf-8")

    def sign_message(self, message):
        payload = str(message).encode('utf-8')
        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        return binascii.hexlify(signature).decode('ascii')

    def sign_transaction(self, transaction_data):
        """Signs the transaction details using the Private Key"""
        return self.sign_message(transaction_data)
