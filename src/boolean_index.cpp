#include "boolean_index.h"
#include "tokenizer.h"
#include "stemmer.h"
#include <iostream>
#include <string>
#include <vector>
#include <sstream>

IndexEntryNode* inverted_index_table[INVERTED_INDEX_HASHTABLE_SIZE] = {nullptr};

unsigned int custom_hash_index(const std::string& s) {
    unsigned int hash = 0;
    for (char c : s) {
        hash = (hash * 31) + c;
    }
    return hash;
}

extern "C" void init_inverted_index() {
    for (int i = 0; i < INVERTED_INDEX_HASHTABLE_SIZE; ++i) {
        inverted_index_table[i] = nullptr;
    }
}

extern "C" void add_to_inverted_index(const std::string& term, int doc_id) {
    unsigned int index = custom_hash_index(term) % INVERTED_INDEX_HASHTABLE_SIZE;

    IndexEntryNode* current_entry = inverted_index_table[index];
    while (current_entry != nullptr) {
        if (current_entry->term == term) {
            DocListNode* current_doc = current_entry->doc_list_head;
            while (current_doc != nullptr) {
                if (current_doc->doc_id == doc_id) {
                    return;
                }
                current_doc = current_doc->next;
            }
            DocListNode* new_doc_node = new DocListNode();
            new_doc_node->doc_id = doc_id;
            new_doc_node->next = current_entry->doc_list_head;
            current_entry->doc_list_head = new_doc_node;
            return;
        }
        current_entry = current_entry->next;
    }

    IndexEntryNode* new_entry_node = new IndexEntryNode();
    new_entry_node->term = term;
    new_entry_node->next = inverted_index_table[index];
    inverted_index_table[index] = new_entry_node;

    DocListNode* new_doc_node = new DocListNode();
    new_doc_node->doc_id = doc_id;
    new_doc_node->next = nullptr;
    new_entry_node->doc_list_head = new_doc_node;
}

extern "C" void cleanup_inverted_index() {
    for (int i = 0; i < INVERTED_INDEX_HASHTABLE_SIZE; ++i) {
        IndexEntryNode* current_entry = inverted_index_table[i];
        while (current_entry != nullptr) {
            DocListNode* current_doc = current_entry->doc_list_head;
            while (current_doc != nullptr) {
                DocListNode* to_delete_doc = current_doc;
                current_doc = current_doc->next;
                delete to_delete_doc;
            }
            IndexEntryNode* to_delete_entry = current_entry;
            current_entry = current_entry->next;
            delete to_delete_entry;
        }
        inverted_index_table[i] = nullptr;
    }
}

extern "C" void print_inverted_index() {
    std::cout << "\n--- Inverted Index Contents ---\n";
    for (int i = 0; i < INVERTED_INDEX_HASHTABLE_SIZE; ++i) {
        IndexEntryNode* current_entry = inverted_index_table[i];
        while (current_entry != nullptr) {
            std::cout << "Term: " << current_entry->term << " -> Doc IDs: ";
            DocListNode* current_doc = current_entry->doc_list_head;
            while (current_doc != nullptr) {
                std::cout << current_doc->doc_id << " ";
                current_doc = current_doc->next;
            }
            std::cout << "\n";
            current_entry = current_entry->next;
        }
    }
    std::cout << "--- End Inverted Index Contents ---\n\n";
}

extern "C" DocListNode* find_term_in_index(const std::string& term) {
    unsigned int index = custom_hash_index(term) % INVERTED_INDEX_HASHTABLE_SIZE;
    IndexEntryNode* current_entry = inverted_index_table[index];
    while (current_entry != nullptr) {
        if (current_entry->term == term) {
            return current_entry->doc_list_head;
        }
        current_entry = current_entry->next;
    }
    return nullptr;
}

extern "C" DocListNode* create_doc_node(int doc_id) {
    DocListNode* newNode = new DocListNode();
    newNode->doc_id = doc_id;
    newNode->next = nullptr;
    return newNode;
}

extern "C" void free_doc_list(DocListNode* head) {
    DocListNode* current = head;
    while (current != nullptr) {
        DocListNode* toDelete = current;
        current = current->next;
        delete toDelete;
    }
}

extern "C" DocListNode* copy_doc_list(DocListNode* head) {
    if (head == nullptr) {
        return nullptr;
    }
    DocListNode* newHead = create_doc_node(head->doc_id);
    DocListNode* currentNew = newHead;
    DocListNode* currentOld = head->next;
    while (currentOld != nullptr) {
        currentNew->next = create_doc_node(currentOld->doc_id);
        currentNew = currentNew->next;
        currentOld = currentOld->next;
    }
    return newHead;
}


extern "C" DocListNode* intersect_doc_lists(DocListNode* list1, DocListNode* list2) {
    DocListNode* resultHead = nullptr;
    DocListNode* resultTail = nullptr;

    DocListNode* temp1 = list1;
    while (temp1 != nullptr) {
        DocListNode* temp2 = list2;
        while (temp2 != nullptr) {
            if (temp1->doc_id == temp2->doc_id) {
                DocListNode* check = resultHead;
                bool isDuplicate = false;
                while (check != nullptr) {
                    if (check->doc_id == temp1->doc_id) {
                        isDuplicate = true;
                        break;
                    }
                    check = check->next;
                }
                if (!isDuplicate) {
                    if (resultHead == nullptr) {
                        resultHead = create_doc_node(temp1->doc_id);
                        resultTail = resultHead;
                    } else {
                        resultTail->next = create_doc_node(temp1->doc_id);
                        resultTail = resultTail->next;
                    }
                }
                break;
            }
            temp2 = temp2->next;
        }
        temp1 = temp1->next;
    }
    return resultHead;
}

extern "C" DocListNode* difference_doc_lists(DocListNode* list1, DocListNode* list2) {
    DocListNode* resultHead = nullptr;
    DocListNode* resultTail = nullptr;

    DocListNode* temp1 = list1;
    while (temp1 != nullptr) {
        DocListNode* temp2 = list2;
        bool foundInList2 = false;
        while (temp2 != nullptr) {
            if (temp1->doc_id == temp2->doc_id) {
                foundInList2 = true;
                break;
            }
            temp2 = temp2->next;
        }

        if (!foundInList2) {
            DocListNode* check = resultHead;
            bool isDuplicate = false;
            while (check != nullptr) {
                if (check->doc_id == temp1->doc_id) {
                    isDuplicate = true;
                    break;
                }
                check = check->next;
            }
            if (!isDuplicate) {
                if (resultHead == nullptr) {
                    resultHead = create_doc_node(temp1->doc_id);
                    resultTail = resultHead;
                } else {
                    resultTail->next = create_doc_node(temp1->doc_id);
                    resultTail = resultTail->next;
                }
            }
        }
        temp1 = temp1->next;
    }
    return resultHead;
}

extern "C" DocListNode* boolean_search(const char* query_cstr) {
    std::string query_str(query_cstr);
    std::stringstream ss(query_str);
    std::string token_str;

    DocListNode* current_results = nullptr;
    bool first_term_processed = false;

    while (ss >> token_str) {
        bool is_not = false;
        if (token_str == "NOT" || (token_str.length() > 1 && token_str[0] == '-')) {
            is_not = true;
            if (token_str == "NOT") {
                if (!(ss >> token_str)) {
                    continue;
                }
            } else {
                token_str = token_str.substr(1);
            }
        }
        
        std::string stemmed_token = stem(token_str);
        if (stemmed_token.empty()) {
            continue;
        }

        DocListNode* docs_for_term = find_term_in_index(stemmed_token);
        
        if (!first_term_processed) {
            if (!is_not) {
                current_results = copy_doc_list(docs_for_term);
            } else {
                current_results = nullptr;
            }
            first_term_processed = true;
        } else {
            if (!is_not) {
                DocListNode* intersected_list = intersect_doc_lists(current_results, docs_for_term);
                free_doc_list(current_results);
                current_results = intersected_list;
            } else {
                DocListNode* diff_list = difference_doc_lists(current_results, docs_for_term);
                free_doc_list(current_results);
                current_results = diff_list;
            }
        }

        if (current_results == nullptr) {
            break;
        }
    }
    return current_results;
}