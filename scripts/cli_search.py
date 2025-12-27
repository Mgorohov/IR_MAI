import pymongo
import json
import os
from ctypes import cdll, c_char_p, c_int, c_void_p, Structure, POINTER, cast

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
lib_path = os.path.join(project_root, "libir_system.so")

try:
    lib = cdll.LoadLibrary(lib_path)
except OSError as e:
    print(f"Error: Could not load libir_system.so: {e}. Make sure it's compiled and in the project root.")
    exit(1)

lib.init_inverted_index.argtypes = []
lib.init_inverted_index.restype = None

lib.build_index_for_document_with_zipf.argtypes = [c_char_p, c_int]
lib.build_index_for_document_with_zipf.restype = None

lib.build_index_for_document.argtypes = [c_char_p, c_int]
lib.build_index_for_document.restype = None

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

def cli_search_interface():
    client = None
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        lib.init_inverted_index()
        print("C++ Inverted Index Initialized.")

        documents_cursor = collection.find({})
        doc_map = {}
        for doc_id, document in enumerate(documents_cursor):
            doc_map[doc_id] = {"title": document.get("title", "N/A"), "url": document.get("url", "N/A")}
            if "content" in document:
                content_bytes = document["content"].encode('utf-8')
                lib.build_index_for_document(content_bytes, doc_id)
        
        print("Index built. Ready for queries.")
        print("Supported logic: implicit AND (e.g., \"word1 word2\"), explicit NOT (e.g., \"word1 NOT word2\" or \"word1 -word2\").")

        while True:
            query = input("Enter search query (or 'q' to quit): ")
            if query.lower() == 'q':
                break
            if not query.strip():
                continue

            query_bytes = query.encode('utf-8')
            result_list_ptr = lib.boolean_search(query_bytes)
            
            if not result_list_ptr:
                search_results_ids = []
            else:
                search_results_ids = parse_doc_list(result_list_ptr)
                lib.free_doc_list(result_list_ptr)

            if not search_results_ids:
                print("No documents found for your query.")
            else:
                print(f"Found {len(search_results_ids)} documents:")
                for doc_id in search_results_ids:
                    doc_info = doc_map.get(doc_id, {"title": "N/A", "url": "N/A"})
                    print(f"  Document ID: {doc_id}")
                    print(f"    Title: {doc_info['title']}")
                    print(f"    URL: {doc_info['url']}")
                    print("---------------------------------------------------")
            print("\n")

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
    cli_search_interface()
