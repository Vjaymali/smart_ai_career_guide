# Create file: test_mysql.py
try:
    import mysql.connector
except ImportError:
    print("❌ Error: mysql.connector not found. Install with: pip install mysql-connector-python")
    exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None
import os

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    
    if connection.is_connected():
        print("✅ MySQL connection successful!")
        
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        print("\n📋 Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        connection.close()
        
except Exception as e:
    print(f"❌ Error: {e}")