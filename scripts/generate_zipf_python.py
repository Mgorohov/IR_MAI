#!/usr/bin/env python3

import pymongo
import re
from collections import Counter
import os
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_dir = os.path.join(project_root, "data")
zipf_csv_path = os.path.join(data_dir, "zipf.csv")

os.makedirs(data_dir, exist_ok=True)

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ir_system"
COLLECTION_NAME = "documents"

def simple_tokenize(text):
    tokens = re.findall(r'\b[a-z]+\b', text.lower())
    return tokens

def simple_stem(word):
    if len(word) > 3:
        if word.endswith('ing'):
            word = word[:-3]
        elif word.endswith('ed'):
            word = word[:-2]
        elif word.endswith('s'):
            word = word[:-1]
    return word

def generate_zipf_data():
    client = None
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        print("Reading documents from MongoDB...")
        word_frequencies = Counter()
        
        documents = collection.find({})
        doc_count = 0
        for document in documents:
            if "content" in document:
                content = document["content"]
                tokens = simple_tokenize(content)
                for token in tokens:
                    stemmed = simple_stem(token)
                    if len(stemmed) > 0:
                        word_frequencies[stemmed] += 1
                doc_count += 1
        
        print(f"Processed {doc_count} documents.")
        print(f"Found {len(word_frequencies)} unique words.")
        
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        print("Generating Zipf data...")
        with open(zipf_csv_path, 'w') as f:
            f.write("rank,freq,zipf_approx\n")
            
            if sorted_words:
                C = float(sorted_words[0][1])
                
                for rank, (word, freq) in enumerate(sorted_words, start=1):
                    zipf_approx = C / rank
                    f.write(f"{rank},{freq},{zipf_approx}\n")
        
        print(f"Zipf's law data saved to {zipf_csv_path}")
        print(f"Top 10 words: {sorted_words[:10]}")
        
    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}. Please ensure MongoDB is running.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    generate_zipf_data()

