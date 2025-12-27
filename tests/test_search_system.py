import unittest
import subprocess
import os
import json
import time
import pymongo
from ctypes import cdll, c_char_p, c_int, c_void_p, Structure, POINTER, cast

# Configuration
PYTHON_CLI_SCRIPT = "scripts/cli_search.py"
PYTHON_DOWNLOAD_SCRIPT = "scripts/download_documents.py"
PYTHON_LOAD_SCRIPT = "scripts/load_to_mongodb.py"
DOCUMENTS_DIR = "data/documents"
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ir_system"
COLLECTION_NAME = "documents"

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

class TestSearchSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure MongoDB is clean and documents are loaded for tests
        print("\n--- Setting up test environment ---")
        cls.client = pymongo.MongoClient(MONGO_URI)
        cls.db = cls.client[DATABASE_NAME]
        cls.collection = cls.db[COLLECTION_NAME]
        cls.collection.delete_many({}) # Clear MongoDB collection

        # Clear local documents directory
        if os.path.exists(DOCUMENTS_DIR):
            for f in os.listdir(DOCUMENTS_DIR):
                os.remove(os.path.join(DOCUMENTS_DIR, f))
        else:
            os.makedirs(DOCUMENTS_DIR)

        # Set LD_LIBRARY_PATH for subprocesses
        cls.env = os.environ.copy()
        lib_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
        cls.project_root = os.path.abspath(os.path.join(lib_path, '..'))
        if 'LD_LIBRARY_PATH' in cls.env:
            cls.env['LD_LIBRARY_PATH'] = f"{cls.project_root}:{cls.env['LD_LIBRARY_PATH']}"
        else:
            cls.env['LD_LIBRARY_PATH'] = cls.project_root
        print(f"Set LD_LIBRARY_PATH to: {cls.env['LD_LIBRARY_PATH']}")

        # Temporarily modify download script to fetch 5 documents for testing
        cls.modify_download_script(5)
        print("Downloading test documents...")
        subprocess.run(["python3", PYTHON_DOWNLOAD_SCRIPT], check=True, cwd=cls.project_root)
        print("Loading test documents to MongoDB...")
        subprocess.run(["python3", PYTHON_LOAD_SCRIPT], check=True, cwd=cls.project_root)
        print("--- Test environment setup complete ---\n")

        # --- Load C++ library and build index directly in the test runner ---
        try:
            cls.lib = cdll.LoadLibrary(os.path.join(cls.project_root, "libir_system.so"))
        except OSError as e:
            print(f"Error loading libir_system.so in tests: {e}")
            raise

        cls.lib.init_inverted_index.argtypes = []
        cls.lib.build_index_for_document.argtypes = [c_char_p, c_int]
        cls.lib.cleanup_inverted_index.argtypes = []
        cls.lib.boolean_search.argtypes = [c_char_p]
        cls.lib.boolean_search.restype = c_void_p
        cls.lib.free_doc_list.argtypes = [c_void_p] # Add argtype for free_doc_list

        cls.lib.init_inverted_index.restype = None
        cls.lib.build_index_for_document.restype = None
        cls.lib.cleanup_inverted_index.restype = None
        cls.lib.free_doc_list.restype = None


        cls.lib.init_inverted_index()
        print("C++ Inverted Index Initialized for direct testing.")

        documents_cursor = cls.collection.find({})
        cls.doc_map = {} # Store basic doc info for display
        for doc_id, document in enumerate(documents_cursor):
            cls.doc_map[doc_id] = {"title": document.get("title", "N/A"), "url": document.get("url", "N/A")}
            if "content" in document:
                content_bytes = document["content"].encode('utf-8')
                cls.lib.build_index_for_document(content_bytes, doc_id)
        print(f"Index built with {len(cls.doc_map)} documents for direct testing.")
        # --- End C++ library loading and index building ---


    @classmethod
    def tearDownClass(cls):
        # Clean up C++ index memory
        cls.lib.cleanup_inverted_index()
        print("C++ Inverted Index memory cleaned up for direct testing.")

        # Clean up MongoDB and restore download script
        print("\n--- Tearing down test environment ---")
        cls.collection.delete_many({}) # Clear MongoDB again
        if os.path.exists(DOCUMENTS_DIR):
            for f in os.listdir(DOCUMENTS_DIR):\
                os.remove(os.path.join(DOCUMENTS_DIR, f))
        cls.restore_download_script()
        cls.client.close()
        print("--- Test environment teardown complete ---")

    @classmethod
    def modify_download_script(cls, num_docs):
        with open(PYTHON_DOWNLOAD_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace max_documents=X with num_docs
        modified_content = content.replace(f"max_documents={20})", f"max_documents={num_docs})")
        with open(PYTHON_DOWNLOAD_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(modified_content)

    @classmethod
    def restore_download_script(cls):
        with open(PYTHON_DOWNLOAD_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace max_documents=X with original 20
        modified_content = content.replace(f"max_documents={5})", f"max_documents={20})")
        with open(PYTHON_DOWNLOAD_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(modified_content)

    def test_single_word_query(self):
        print("Testing single word query directly with C++ library...")
        query = "book"
        query_bytes = query.encode('utf-8')
        result_list_ptr = self.lib.boolean_search(query_bytes)
        search_results_ids = parse_doc_list(result_list_ptr)
        self.lib.free_doc_list(result_list_ptr) # Free C++ list memory

        self.assertGreater(len(search_results_ids), 0)
        print(f"Direct search results for \"{query}\": {search_results_ids}")

    def test_multiple_word_query(self):
        print("Testing multiple word query (AND logic) directly with C++ library...")
        query = "the book"
        query_bytes = query.encode('utf-8')
        result_list_ptr = self.lib.boolean_search(query_bytes)
        search_results_ids = parse_doc_list(result_list_ptr)
        self.lib.free_doc_list(result_list_ptr) # Free C++ list memory

        self.assertGreater(len(search_results_ids), 0)
        # With AND logic, the number of results should be <= total documents (5)
        self.assertLessEqual(len(search_results_ids), 5)
        print(f"Direct search results for \"{query}\": {search_results_ids}")


    def test_no_results_query(self):
        print("Testing query with no expected results directly with C++ library...")
        query = "nonexistentwordxyz123"
        query_bytes = query.encode('utf-8')
        result_list_ptr = self.lib.boolean_search(query_bytes)
        search_results_ids = parse_doc_list(result_list_ptr)
        self.lib.free_doc_list(result_list_ptr) # Free C++ list memory

        self.assertEqual(len(search_results_ids), 0)
        print(f"Direct search results for \"{query}\": {search_results_ids}")

    def test_empty_query(self):
        print("Testing empty query directly with C++ library...")
        query = ""
        query_bytes = query.encode('utf-8')
        result_list_ptr = self.lib.boolean_search(query_bytes)
        search_results_ids = parse_doc_list(result_list_ptr)
        self.lib.free_doc_list(result_list_ptr) # Free C++ list memory

        self.assertEqual(len(search_results_ids), 0) # Empty query should return no results
        print(f"Direct search results for \"{query}\": {search_results_ids}")

    def test_not_operator_query(self):
        print("Testing NOT operator query directly with C++ library...")
        # Find a common word and a word that might exclude some documents
        # Assuming "the" is in all documents, and "book" is in most.
        # Let's try to find documents with "the" but NOT "book".
        query = "the NOT book"
        query_bytes = query.encode('utf-8')
        result_list_ptr = self.lib.boolean_search(query_bytes)
        search_results_ids = parse_doc_list(result_list_ptr)
        self.lib.free_doc_list(result_list_ptr) # Free C++ list memory

        # We expect fewer documents than just "the", and possibly 0 if "book" is in all "the" documents.
        # Given the sample documents are books, it's highly likely "book" is in all of them.
        # So, "the NOT book" should return 0 results.
        self.assertEqual(len(search_results_ids), 0)
        print(f"Direct search results for \"{query}\": {search_results_ids}")

if __name__ == '__main__':
    unittest.main()
