import pymongo
import os
import json

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ir_system"
COLLECTION_NAME = "documents"
DOCUMENTS_DIR = "data/documents"

def load_documents_to_mongodb(mongo_uri, db_name, collection_name, documents_dir):
    client = None
    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        collection.delete_many({})
        print(f"Cleared existing documents in {db_name}.{collection_name}")

        documents_loaded = 0
        for filename in os.listdir(documents_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(documents_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    document_data = json.load(f)
                    collection.insert_one(document_data)
                    documents_loaded += 1
        print(f"Successfully loaded {documents_loaded} documents into {db_name}.{collection_name}")

    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}. Please ensure MongoDB is running.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    load_documents_to_mongodb(MONGO_URI, DATABASE_NAME, COLLECTION_NAME, DOCUMENTS_DIR)

