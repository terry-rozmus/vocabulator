import os
import re
from .abbreviations import abbreviations
from .syllables import syllables


class Vocabulary():
    """Class to establish attributes and methods associated with all vocabulary objects
    containing word frequency data."""

    def __init__(self):
        self._frequency_dict = {}
        self._is_active = True
        self._total_count = 0
        self._syllables_found = False

    def _make_frequency_dict(self, word_list):
        # Make a dictionary which has frequency data for each word in line_list.
        self._frequency_dict = {}
        for word in word_list:
            if word not in self._frequency_dict:
                self._frequency_dict[word] = word_list.count(word)
                self._total_count += self._frequency_dict[word]

    def _del_word(self, word):
        if word in self._frequency_dict:
            del self._frequency_dict[word]

    def word_exists(self, word):
        return word in self._frequency_dict

    def vowel_count(self, word):
        count = 0
        count += word.count('a')
        count += word.count('e')
        count += word.count('i')
        count += word.count('o')
        count += word.count('u')
        count += word.count('y', 1)
        return count

    def has_real_syllables(self, string):
        # Call recursive find syllables function and return value.
        return (self.divide_syllables(string) != None)

    def divide_syllables(self, string):
        # Prepare for testing if word contains all valid syllables
        self._syllables_found = False
        # Call recursive find syllables function and return value.
        return self._find_syllables(string)

    def _find_syllables(self, string):
        length = len(string)
        # Iterate over left substrings of decreasing length until a valid syllable is found.
        for i in range(length, -1, -1):
            left = string[0:i+1]
            right = string[i+1:length]
            # print left + ' ' + right
            # Check if the left substring is a valid syllable.
            if left in syllables:
                if right != '':
                    # Check if the right substring is not a valid end syllable.
                    if right not in syllables:
                        # Recursive call to find the next valid left and right substrings from the current iteration's
                        # right substring (which is the new string in the recursive call).
                        right = self._find_syllables(right)
                    else:
                        # Terminating case is where the right is in the valid syllables list
                        self._syllables_found = True
                    if self._syllables_found:
                        # Collect the contents of left and right substrings back through the whole recursive chain.
                        return left + '/' + right
                else:
                    # This is a valid word with a single syllable
                    return left

    def get_frequency_dict(self):
        # Return the whole frequency dictionary.
        return self._frequency_dict

    def get_word_count(self, word, check_active=False):
        # Return the count of a single word in this vocabulary object.
        if (self._is_active or not check_active) and word in self._frequency_dict:
            return self._frequency_dict[word]
        else:
            return 0

    def get_total_count(self):
        return self._total_count


class VocabularyList(Vocabulary):
    """Class to add additional properties and methods to the Vocabulary object needed
    for dealing with short lists."""

    def __init__(self):
        # Initialise the vocabulary base class
        Vocabulary.__init__(self)

        self._frequency_dict = {}
        self._is_active = True
        self._total_count = 0

    def _make_word_list(self, line_list):
        # Output a new list by splitting the input line_list on any white-space
        # character or any punctuation character except hyphens or apostrophes.
        word_list = []
        for line in line_list:
            # Replace any non-ascii hyphens with the ascii one
            line = line.replace(u'\u2019', "'")

            # Check for vocabulary list words with (*) on the end containing lowercase
            # letters indicating alternate forms and separate them into two words.
            conjugated_words = re.findall("[a-z'\-]+\([a-z'\-]+\)", line)
            for word in conjugated_words:
                pieces = word.split('(')
                two_words = pieces[0] + ' ' + pieces[0] + pieces[1].rstrip(')')
                line = line.replace(word, two_words)

            # Eliminate vocabulary list words with [*] unless there is a '.', '?' or '!'
            # These usually contain phonetic spellings in English education textbooks in Japan.
            # Also test for '|' in place of '[' an ']' because OCR software sometimes confuses
            # these symbols.
            line = re.sub('[\[\|][^\]\|]+[^\?\!\.][\]\|]', '', line)

            #  Build the new word list by splitting the line on any character
            # that is not a lowercase letter, a hyphen or an apostrophe.
            # word_list += re.split("[^a-z'\-]+", line)
            line_words = re.split("[^a-z'\-]+", line)
            for word in line_words:
                word = re.sub("^[-']|[-']$", '', word)
                if word != '' and (len(word) > 1 or word == 'i' or word == 'a') \
                        and (self.has_real_syllables(word) or word in abbreviations):
                    word_list.append(word)

        return word_list

    def _make_frequency_dict(self, word_list):
        # Make a dictionary which has frequency data for each word in line_list.
        self._frequency_dict = {}
        for word in word_list:
            if word not in self._frequency_dict:
                self._frequency_dict[word] = word_list.count(word)
                self._total_count += self._frequency_dict[word]

    def _del_word(self, word):
        if word in self._frequency_dict:
            del self._frequency_dict[word]

    def get_frequency_dict(self):
        # Return the whole frequency dictionary.
        return self._frequency_dict

    def get_word_count(self, word, check_active=False):
        # Return the frequency of a single word in this vocabulary object.
        if (self._is_active or not check_active) and word in self._frequency_dict:
            return self._frequency_dict[word]
        else:
            return 0


class VocabularyProcess(VocabularyList):
    """Class to build a vocabulary dictionary containing word frequency data
    from a text line in a DB containing sentences, paragraphs or lists."""

    def __init__(self, input_text_list):
        # Initialise the vocabulary list base class
        VocabularyList.__init__(self)

        # Make a word list from the inputted text list.
        word_list = self._make_word_list(input_text_list)

        # Make the vocabulary frequency list.
        self._make_frequency_dict(word_list)

        # Delete empty word
        self._del_word('')


class VocabularyBox(VocabularyList):
    """This class is for creating a vocabulary object from a screen input line."""

    def __init__(self, input_text):
        # Initialise vocabulary list base class
        VocabularyList.__init__(self)

        # Make a word list from the input text.
        word_list = self._make_word_list(input_text)

        # Make the vocabulary frequency list.
        self._make_frequency_dict(word_list)

        # Delete empty word
        self._del_word('')
