from pymongo import MongoClient
import json
import os
import ijson
from tqdm import tqdm
from decimal import Decimal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "rag", "data")

DB_NAME = "smartlp"

def load_json(file_name):
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

def stream_json_to_mongo(file_name, collection, batch_size=1000):
    path = os.path.join(DATA_DIR, file_name)
    count = 0
    batch = []

    with open(path, "r", encoding="utf-8") as f:
        objects = ijson.items(f, "item")  # assumes top-level JSON array
        for obj in tqdm(objects, desc=f"Ingesting {file_name}"):
            obj = convert_decimals(obj)
            # remove oid if present
            if '_id' in obj:
                del obj['_id']
            batch.append(obj)
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                count += len(batch)
                batch = []
        if batch:
            collection.insert_many(batch)
            count += len(batch)

    print(f"Finished inserting {count} documents into {collection.name}")

def main():
    client = MongoClient("mongodb://localhost:27017/?directConnection=true")
    db = client[DB_NAME]

    # Collections
    kb_col = db["knowledge_base"]
    kb_col.drop()
    stream_json_to_mongo("knowledge_base.json", kb_col)
    settings_col = db["settings"]
    settings_col.drop()
    stream_json_to_mongo("settings.json", settings_col)

    vector_index = {
        'name': 'vector_index',
        'type': 'vectorSearch',
        'definition': {
            'fields': [
                {'type': 'vector', 'path': 'embedding', 'numDimensions': 384, 'similarity': 'cosine'},
                {'type': 'filter', 'path': 'metadata.category'}
            ]
        }
    }

    text_index = {
        'name': 'text_index',
        'type': 'search',
        'definition': {'mappings': {'dynamic': True}}
    }

    try:
        kb_col.create_search_index(vector_index)
        print("Vector index created.")
    except Exception as e:
        print("Vector index creation failed:", e)

    try:
        kb_col.create_search_index(text_index)
        print("Text index created.")
    except Exception as e:
        print("Text index creation failed:", e)

if __name__ == "__main__":
    main()
