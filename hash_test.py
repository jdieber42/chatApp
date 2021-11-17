import hashlib

password = "123456"

password1 = "asdhgasjkdgsajdgsahdghsagdhsgadhjasgdkjhsajkdh"

hashed_password = hashlib.sha256(password.encode()).hexdigest()

hashed_password1 = hashlib.sha256(password1.encode()).hexdigest()

print(hashed_password)

print(hashed_password1)