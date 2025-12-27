from flask import Flask, render_template, request
import pymongo
import json
import os
from ctypes import cdll, c_char_p, c_int, c_void_p, Structure, POINTER, cast

app = Flask(__name__, template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')))

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

lib.boolean_search.argtypes = [c_char_p]
lib.boolean_search.restype = c_void_p

lib.free_doc_list.argtypes = [c_void_p]
lib.free_doc_list.restype = None

lib.init_hash_table.argtypes = []
lib.init_hash_table.restype = None


class DocListNode(Structure):
    _fields_ = [("doc_id", c_int),
                ("next", c_void_p)]

def parse_doc_list(doc_list_ptr):
    results = []
    current_node = cast(doc_list_ptr, POINTER(DocListNode))
    while current_node and current_node.contents.doc_id >= 0:
        results.append(current_node.contents.doc_id)
        current_node = cast(current_node.contents.next, POINTER(DocListNode))
    return results

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ir_system"
COLLECTION_NAME = "documents"

doc_map = {}

def initialize_search_engine():
    client = None
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        lib.init_inverted_index()
        print("C++ Inverted Index Initialized.")

        documents_cursor = collection.find({})
        for doc_id, document in enumerate(documents_cursor):
            doc_map[doc_id] = {"title": document.get("title", "N/A"), "url": document.get("url", "N/A")}
            if "content" in document:
                content_bytes = document["content"].encode('utf-8')
                lib.build_index_for_document(content_bytes, doc_id)
        
        print(f"Index built with {len(doc_map)} documents. Ready for web queries.")

    except pymongo.errors.ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}. Please ensure MongoDB is running.")
        exit(1)
    except Exception as e:
        print(f"An error occurred during index initialization: {e}")
        exit(1)
    finally:
        if client:
            client.close()

with app.app_context():
    initialize_search_engine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    search_results_display = []

    if query:
        query_bytes = query.encode('utf-8')
        result_list_ptr = lib.boolean_search(query_bytes)
        
        if not result_list_ptr:
            search_results_ids = []
        else:
            search_results_ids = parse_doc_list(result_list_ptr)
            lib.free_doc_list(result_list_ptr)

        for doc_id in search_results_ids:
            doc_info = doc_map.get(doc_id, {"title": "N/A", "url": "N/A"})
            search_results_display.append({
                "id": doc_id,
                "title": doc_info["title"],
                "url": doc_info["url"]
            })

    return render_template('index.html', query=query, results=search_results_display)

if __name__ == '__main__':
    import atexit
    atexit.register(lambda: (lib.cleanup_inverted_index() and print("C++ Inverted Index memory cleaned up.")) if 'lib' in locals() else None)
    
    app.run(debug=True, host='0.0.0.0')
