#ifndef ZIPF_ANALYZER_H
#define ZIPF_ANALYZER_H

#include <string>
#include <vector>

struct WordFrequency {
    std::string word;
    int frequency;
};

extern "C" void init_hash_table();
extern "C" void add_word_frequency(const std::string& word);
extern "C" std::vector<WordFrequency> analyze_zipf();
extern "C" void save_zipf_to_csv(const std::vector<WordFrequency>& frequencies, const char* filename);


#endif // ZIPF_ANALYZER_H