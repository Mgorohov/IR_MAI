#include "stemmer.h"
#include <string>
#include <vector>
#include <cctype>
#include <algorithm>

bool is_vowel(char c) {
    c = std::tolower(static_cast<unsigned char>(c));
    return (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u');
}

int get_m(const std::string& s) {
    int m = 0;
    bool prev_is_vowel = false;
    for (char c : s) {
        bool current_is_vowel = is_vowel(c);
        if (prev_is_vowel && !current_is_vowel) {
            m++;
        }
        prev_is_vowel = current_is_vowel;
    }
    return m;
}

bool ends_with(const std::string& word, const std::string& suffix) {
    if (word.length() < suffix.length()) {
        return false;
    }
    return word.substr(word.length() - suffix.length()) == suffix;
}

std::string replace_suffix(const std::string& word, const std::string& old_suffix, const std::string& new_suffix) {
    return word.substr(0, word.length() - old_suffix.length()) + new_suffix;
}

std::string stem(const std::string& word) {
    if (word.length() <= 2) {
        return word;
    }

    std::string s = word;

    if (ends_with(s, "sses")) { s = replace_suffix(s, "sses", "ss"); }
    else if (ends_with(s, "ies")) { s = replace_suffix(s, "ies", "i"); }
    else if (ends_with(s, "ss")) { }
    else if (ends_with(s, "s")) { s = replace_suffix(s, "s", ""); }

    bool changed_1b = false;
    if (ends_with(s, "eed")) {
        if (get_m(replace_suffix(s, "eed", "")) > 0) { s = replace_suffix(s, "eed", "ee"); changed_1b = true; }
    } else if (ends_with(s, "ed")) {
        s = replace_suffix(s, "ed", ""); changed_1b = true;
    } else if (ends_with(s, "ing")) {
        s = replace_suffix(s, "ing", ""); changed_1b = true;
    }

    if (changed_1b) {
        if (ends_with(s, "at") || ends_with(s, "bl") || ends_with(s, "iz")) { s += "e"; }
        else if (s.length() > 1 && !is_vowel(s[s.length()-1]) && is_vowel(s[s.length()-2]) && !is_vowel(s[s.length()-3]) && s[s.length()-1] != 'l' && s[s.length()-1] != 's' && s[s.length()-1] != 'z') { s = s.substr(0, s.length() - 1); }
        else if (s.length() == 1 && is_vowel(s[0])) { }
    }

    if (ends_with(s, "y")) {
        if (s.length() > 1 && !is_vowel(s[s.length() - 2])) {
            s = replace_suffix(s, "y", "i");
        }
    }

    return s;
}
