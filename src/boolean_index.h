#ifndef BOOLEAN_INDEX_H
#define BOOLEAN_INDEX_H

#include <string>

struct DocListNode {
    int doc_id;
    DocListNode* next;
};

struct IndexEntryNode {
    std::string term;
    DocListNode* doc_list_head;
    IndexEntryNode* next;
};

const int INVERTED_INDEX_HASHTABLE_SIZE = 10000;

extern IndexEntryNode* inverted_index_table[INVERTED_INDEX_HASHTABLE_SIZE];

extern "C" void init_inverted_index();
extern "C" void add_to_inverted_index(const std::string& term, int doc_id);
extern "C" void cleanup_inverted_index();
extern "C" void print_inverted_index();
extern "C" DocListNode* boolean_search(const char* query_cstr);
extern "C" void free_doc_list(DocListNode* head);
extern "C" DocListNode* create_doc_node(int doc_id);
extern "C" DocListNode* copy_doc_list(DocListNode* head);
extern "C" DocListNode* intersect_doc_lists(DocListNode* list1, DocListNode* list2);
extern "C" DocListNode* difference_doc_lists(DocListNode* list1, DocListNode* list2);

#endif // BOOLEAN_INDEX_H

