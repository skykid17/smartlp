import os
import sys
from pymongo import MongoClient

url = os.getenv('MONGO_URL') or os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
db_name = os.getenv('MONGO_DB_NAME') or 'soc_rag_db'

print(f'Using Mongo URL: {url}')
print(f'Using database: {db_name}')

try:
    client = MongoClient(url, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client.get_database(db_name)
    names = db.list_collection_names()
    print('Collections:', names)
    for col in ('config', 'logs'):
        if col in names:
            try:
                cnt = db[col].count_documents({})
                print(f"'{col}' count: {cnt}")
            except Exception as e:
                print(f"Error counting '{col}': {e}")
        else:
            print(f"'{col}' NOT FOUND")
except Exception as exc:
    print('Connection/Query error:', exc)
    sys.exit(1)
