import logging.config
import os

import searching
import parsing

if not os.path.isdir("log"):
    os.mkdir('log')
logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)


def parse_and_index(base_dir):
    # STEP 1: Parse html files
    docs = parsing.UCLParser().parse(base_dir)

    # STEP 2: Index documents
    searching.index_docs(list(docs))


def search(query):
    results = searching.search(query, limit=20, ranking='pagerank')
    return results


# 1. Parse and index (We only need to do this once, as the index file will be saved on disk and used for searching)
# Uncomment the following two lines and change base_dir to the root directory of local website folder

base_dir = "C:\\Users\\andre\\Desktop\\UCL W\\CS.UCL\\"
parse_and_index(base_dir)


# 2. Search query
results = search('study abroad meng')

# Simply print search results
for i, result in enumerate(results):
    print(i+1, '\n', result)








