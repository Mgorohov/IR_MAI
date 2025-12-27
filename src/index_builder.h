#ifndef INDEX_BUILDER_H
#define INDEX_BUILDER_H

#include <string>

extern "C" void build_index_for_document(const char* text, int doc_id);
extern "C" void build_index_for_document_with_zipf(const char* text, int doc_id);

#endif // INDEX_BUILDER_H