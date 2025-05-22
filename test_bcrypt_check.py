import bcrypt

pw = "Test1234!"
hashed = "$2b$12$5UZNlAIWSAmcMOf2hoe9vO4fHK7YJaaEzo8HIvntBqu7rFOJCccqq"
print("pw:", pw)
print("hashed:", hashed)
print("checkpw:", bcrypt.checkpw(pw.encode(), hashed.encode())) 