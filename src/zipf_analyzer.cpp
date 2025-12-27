#include "zipf_analyzer.h"
#include <vector>
#include <string>
#include <algorithm>
#include <iostream>
#include <fstream>

unsigned int custom_hash(const std::string& s) {
    unsigned int hash = 0;
    for (char c : s) {
        hash = (hash * 31) + c;
    }
    return hash;
}

struct HashTableNode {
    std::string word;
    int frequency;
    HashTableNode* next;
};

const int HASH_TABLE_SIZE = 1000;

HashTableNode* hash_table[HASH_TABLE_SIZE] = {nullptr}; 

extern "C" void init_hash_table() {
    for (int i = 0; i < HASH_TABLE_SIZE; ++i) {
        HashTableNode* current = hash_table[i];
        while (current != nullptr) {
            HashTableNode* to_delete = current;
            current = current->next;
            delete to_delete;
        }
        hash_table[i] = nullptr;
    }
    std::cout << "Zipf hash table initialized and cleared." << std::endl;
}

extern "C" void add_word_frequency(const std::string& word) {
    if (word.empty()) {
        return;
    }
    unsigned int index = custom_hash(word) % HASH_TABLE_SIZE;

    HashTableNode* current = hash_table[index];
    while (current != nullptr) {
        if (current->word == word) {
            current->frequency++;
            return;
        }
        current = current->next;
    }

    HashTableNode* new_node = new HashTableNode();
    new_node->word = word;
    new_node->frequency = 1;
    new_node->next = hash_table[index];
    hash_table[index] = new_node;
}

bool compareWordFrequency(const WordFrequency& a, const WordFrequency& b) {
    return a.frequency > b.frequency;
}

extern "C" std::vector<WordFrequency> analyze_zipf() {
    std::vector<WordFrequency> frequencies;
    for (int i = 0; i < HASH_TABLE_SIZE; ++i) {
        HashTableNode* current = hash_table[i];
        while (current != nullptr) {
            frequencies.push_back({current->word, current->frequency});
            current = current->next;
        }
    }

    std::sort(frequencies.begin(), frequencies.end(), compareWordFrequency);

    return frequencies;
}

extern "C" void save_zipf_to_csv(const std::vector<WordFrequency>& frequencies, const char* filename) {
    std::ofstream outfile(filename);
    if (!outfile.is_open()) {
        std::cerr << "Error: Could not open file " << filename << " for writing Zipf data." << std::endl;
        return;
    }

    outfile << "rank,freq,zipf_approx\n";

    if (frequencies.empty()) {
        outfile.close();
        return;
    }

    double C = static_cast<double>(frequencies[0].frequency);

    for (size_t i = 0; i < frequencies.size(); ++i) {
        int rank = i + 1;
        double zipf_approx = C / rank;
        outfile << rank << "," << frequencies[i].frequency << "," << zipf_approx << "\n";
    }

    outfile.close();
    std::cout << "Zipf's law data saved to " << filename << std::endl;
}
