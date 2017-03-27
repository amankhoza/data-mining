import logging.config
import os

from SearchEngine import searching
from SearchEngine import parsing

# Initialize logging
if not os.path.isdir("log"):
    os.mkdir('log')
logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)


def parse_and_index(base_dir):

    # STEP 1: Parse html files
    docs = parsing.UCLParser().parse_files(base_dir)

    # Before creating the index we should run here any other algorithms for including additional document fields:
    # E.g. pagerank_score, <other_scoring_algorithm>_score

    # STEP 2: Index documents
    searching.index_docs(docs)


def search(query):
    results = searching.search(query, limit=10, ranking_algorithm='BM25')
    return results


# 1. Parse and index (Only do this once, and then you can search directly)
# Uncomment the following two lines and change base_dir to the root directory of local website folder
base_dir = "C:\\Users\\andre\\Desktop\\UCL W\\UCL W\\www.ucl.ac.uk\\isd\\"
parse_and_index(base_dir)


# 2. Search query
results = search("Password reset")

# Simply print search results
for i, result in enumerate(results):
    print(i+1, '\n', result)








