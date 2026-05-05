
import pymysql
import hashlib

# MySQL connection
conn = pymysql.connect(
    host='127.0.0.1',
    user='root',
    password='123456',
    database='device',
    charset='utf8mb4'
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM user")
users = cursor.fetchall()
for user in users:
    print(f"User: {user}")

# Check what's MD5 of "1"
md5 = hashlib.md5()
md5.update(b"1")
print(f"\nMD5 of '1': {md5.hexdigest()}")

cursor.close()
conn.close()

