import hashlib

def valid_hash(email: str, github_url: str, nonce: int) -> bool:
    data = (
        email.encode("utf-8") +
        b"\n" +
        github_url.encode("utf-8") +
        b"\n" +
        nonce.to_bytes(8, byteorder="big")
    )
    
    result = hashlib.sha256(data).digest()
    
    return (
        result[0] == 0 and
        result[1] == 0 and
        result[2] == 0 and
        result[3] < 0x10
    )

def mine(email: str, github_url: str) -> int:
    nonce = 0
    
    while True:
        if valid_hash(email, github_url, nonce):
            return nonce
        nonce += 1

if __name__ == "__main__":
    email = "example@student.tudelft.nl"
    github_url = "https://github.com/MateeiB/Blockchain2026"

    # testing
    nonce = mine(email, github_url)
    print(f"Found nonce: {nonce}")
    data = email.encode() + b"\n" + github_url.encode() + b"\n" + nonce.to_bytes(8, byteorder="big")
    print(f"Hash: {hashlib.sha256(data).hexdigest()}")