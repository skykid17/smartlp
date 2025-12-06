import os
import json
from pymongo import MongoClient

url = os.getenv('MONGO_URL') or os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
db_name = os.getenv('MONGO_DB_NAME') or 'soc_rag_db'
print(f'Connecting to: {url} DB: {db_name}')
client = MongoClient(url)
db = client.get_database(db_name)
cols = db.list_collection_names()
print('Collections:', cols)
if 'config' in cols:
    docs = list(db['config'].find({}))
    for d in docs:
        # convert ObjectId
        d = json.loads(json.dumps(d, default=str))
        print(json.dumps(d, indent=2))
else:
    print("No 'config' collection found")
