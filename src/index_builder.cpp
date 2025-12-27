#include "index_builder.h"
#include "tokenizer.h"
#include "stemmer.h"
#include "boolean_index.h"
#include "zipf_analyzer.h"
#include <iostream>
#include <vector>

extern "C" void build_index_for_document(const char* text_cstr, int doc_id) {
    std::string text(text_cstr);
    std::vector<std::string> tokens = tokenize(text);
    for (const std::string& token : tokens) {
        std::string stemmed_token = stem(token);
        if (!stemmed_token.empty()) {
            add_to_inverted_index(stemmed_token, doc_id);
        }
    }
}

extern "C" void build_index_for_document_with_zipf(const char* text_cstr, int doc_id) {
    std::string text(text_cstr);
    std::vector<std::string> tokens = tokenize(text);
    for (const std::string& token : tokens) {
        std::string stemmed_token = stem(token);
        if (!stemmed_token.empty()) {
            add_to_inverted_index(stemmed_token, doc_id);
            add_word_frequency(stemmed_token);
        }
    }
}
