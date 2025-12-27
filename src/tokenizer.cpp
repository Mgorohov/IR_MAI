#include "tokenizer.h"
#include <sstream>
#include <algorithm>
#include <cctype>
#include <iostream>

std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> tokens;
    std::string current_token;
    std::stringstream ss(text);
    char c;

    while (ss.get(c)) {
        if (std::isalnum(static_cast<unsigned char>(c))) {
            current_token += std::tolower(static_cast<unsigned char>(c));
        } else {
            if (!current_token.empty()) {
                tokens.push_back(current_token);
                current_token.clear();
            }
        }
    }
    if (!current_token.empty()) {
        tokens.push_back(current_token);
    }

    return tokens;
}

