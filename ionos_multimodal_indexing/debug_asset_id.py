
import os
import hashlib
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")
DB_DATA_LOCATION = os.getenv("DB_DATA_LOCATION")

print(f"Connecting to DB: {DB_DATABASE_NAME} as {DB_USERNAME}")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_DATABASE_NAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def get_file_checksum(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(8192)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

image_path = "/Users/macenving/immich-server/library/imported/recovered_takeout_2026/Takeout/Google Photos/Photos from 2025/IMG_0048.JPG"

print(f"Checking file: {image_path}")
if not os.path.exists(image_path):
    print("File does not exist!")
    exit(1)

checksum = get_file_checksum(image_path)
print(f"Checksum (SHA1): {checksum}")

conn = get_db_connection()
if not conn:
    print("No DB connection")
    exit(1)

cursor = conn.cursor()
query = sql.SQL("""
    SELECT id, "originalPath" FROM asset
    WHERE checksum = decode(%s, 'hex')
""")
cursor.execute(query, (checksum,))
results = cursor.fetchall()
print(f"Found {len(results)} matches in DB:")
for r in results:
    print(f" - ID: {r[0]} | Path: {r[1]}")

conn.close()
