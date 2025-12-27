import pymongo
import json
import os
from ctypes import cdll, c_char_p, c_int, c_void_p, Structure, POINTER, cast

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_path = os.path.join(project_root, "libir_system.so")
data_dir = os.path.join(project_root, "data")
zipf_csv_path = os.path.join(data_dir, "zipf.csv")

os.makedirs(data_dir, exist_ok=True)

try:
    lib = cdll.LoadLibrary(lib_path)
except OSError as e:
    print(f"Error: Could not load libir_system.so: {e}. Make sure it's compiled and in the project root.")
    exit(1)

class WordFrequencyC(Structure):
    _fields_ = [("word", c_char_p),
                ("frequency", c_int)]

class VectorWordFrequencyC(Structure):
    _fields_ = [
        ("data", POINTER(WordFrequencyC)),
        ("size", c_int),
        ("capacity", c_int)
    ]

lib.init_inverted_index.argtypes = []
lib.init_inverted_index.restype = None

lib.build_index_for_document_with_zipf.argtypes = [c_char_p, c_int]
lib.build_index_for_document_with_zipf.restype = None

lib.cleanup_inverted_index.argtypes = []
lib.cleanup_inverted_index.restype = None

lib.print_inverted_index.argtypes = []
lib.print_inverted_index.restype = None

lib.boolean_search.argtypes = [c_char_p]
lib.boolean_search.restype = c_void_p

lib.free_doc_list.argtypes = [c_void_p]
lib.free_doc_list.restype = None

lib.init_hash_table.argtypes = []
lib.init_hash_table.restype = None

lib.add_word_frequency.argtypes = [c_char_p]
lib.add_word_frequency.restype = None

lib.analyze_zipf.argtypes = []
lib.analyze_zipf.restype = VectorWordFrequencyC

lib.save_zipf_to_csv.argtypes = [VectorWordFrequencyC, c_char_p]
lib.save_zipf_to_csv.restype = None

def parse_doc_list(doc_list_ptr):
    results = []
    class DocListNode(Structure):
        _fields_ = [("doc_id", c_int),
                    ("next", c_void_p)]
    
    current_node = cast(doc_list_ptr, POINTER(DocListNode))
    while current_node and current_node.contents.doc_id >= 0:
        results.append(current_node.contents.doc_id)
        current_node = cast(current_node.contents.next, POINTER(DocListNode))
    return results

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ir_system"
COLLECTION_NAME = "documents"

def build_index_from_mongodb():
    client = None
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        lib.init_inverted_index()
        print("C++ Inverted Index Initialized.")
        
        lib.init_hash_table()
        print("C++ Zipf's law hash table initialized and cleared.")

        documents = collection.find({})
        for doc_id, document in enumerate(documents):
            if "content" in document:
                content_bytes = document["content"].encode('utf-8')
                lib.build_index_for_document_with_zipf(content_bytes, doc_id)
        
        print("Index built. Printing contents (truncated for brevity)...")

        print("\nPerforming Zipf's law analysis...")
        zipf_frequencies_vector = lib.analyze_zipf()
        
        zipf_csv_path_bytes = zipf_csv_path.encode('utf-8')
        lib.save_zipf_to_csv(zipf_frequencies_vector, zipf_csv_path_bytes)
        print(f"Zipf's law data saved to {zipf_csv_path}")

        query = "story book"
        print(f"\nPerforming example search for query: \"{query}\"\n")
        query_bytes = query.encode('utf-8')
        result_list_ptr = lib.boolean_search(query_bytes)
        search_results = parse_doc_list(result_list_ptr)
        print(f"Search results for \"{query}\": {search_results}\n")
        lib.free_doc_list(result_list_ptr)
        print("C++ search result list memory cleaned up.")

    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}. Please ensure MongoDB is running.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if client:
            client.close()
        lib.cleanup_inverted_index()
        print("C++ Inverted Index memory cleaned up.")

if __name__ == "__main__":
    build_index_from_mongodb()
