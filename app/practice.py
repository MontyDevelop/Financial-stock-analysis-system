import hashlib
import os

password = "TraderPass1234!"

# generating 16 bytes of pure random characters

character_ = os.urandom(16).hex()
# print(character_)
# running it throght multiple mathematical processing

hashed_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),bytes.fromhex(character_), 100_000)

stored_value = f"100000${character_}${hashed_bytes.hex()}"

print(f"Original Password: {password}")
print(f"What get saved in the db: {stored_value}")