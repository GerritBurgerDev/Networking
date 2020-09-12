from fuzzywuzzy import process
import os
from os import listdir
from os.path import isfile, join

def search(param):
    query = param.lower()
    file_names = []
    final_results = []

    extensions = []

    for path in listdir("Files"):
        if isfile(join("Files", path)):
            filename, extension = os.path.splitext(path)

            extensions.append(extension)

            file_names.append(path)

    i = 0
    for extension in extensions:
        new_param = ""
        if param[0] == ".":
            new_param = param[1:]

        if new_param != "":
            if new_param in extension:
                final_results.append(file_names[i])
        else:
            if param in extension:
                final_results.append(file_names[i])
        i += 1

    results = process.extract(query, file_names)

    for res in results:
        query_len = len(query)
        word_score = res[1]

        words = res[0].split()
        counts = []
        for word in words:
            word = word.lower()
            counter = 0
            if word[0] == query[0]:
                for char in word:
                    for char_q in query:
                        if char == char_q:
                            counter += 1
                            break
                counts.append(counter)

        if len(counts) != 0:
            max_c = max(counts)
            word_score += (5 * max_c)

        if word_score >= 70:
            final_results.append(res[0])

    final_results = list(set(final_results))

    return final_results
