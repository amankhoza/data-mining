import logging.config
import os

from SearchEngine import searching
from SearchEngine import parsing
from collections import defaultdict

# Initialize logging
if not os.path.isdir("log"):
    os.mkdir('log')
logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)


def parse_and_index(base_dir):

    # STEP 1: Parse html files
    docs = parsing.UCLParser().parse_files(base_dir)

    incoming = defaultdict(list)
    for doc in docs:
        for link in doc.links:
            incoming[link[0]].append(doc.url)

    epochs = 30
    dumping_factor = 0.85
    while epochs > 0:
        for doc in docs:
            interm = 0
            for inc in incoming[doc.url]:
                if len(doc.links) > 0:
                    interm += doc.pagerank / len(doc.links)
            doc.pagerank = (1-dumping_factor) + dumping_factor*interm
        epochs -= 1


    for doc in docs:
        print(doc.url, doc.pagerank, '\n')
    # Before creating the index we should run here any other algorithms for including additional document fields:
    # E.g. pagerank_score, <other_scoring_algorithm>_score

    # STEP 2: Index documents
    searching.index_docs(docs)


def search(query):
    results = searching.search(query, limit=10, ranking_algorithm='BM25')
    return results


# 1. Parse and index (Only do this once, and then you can search directly)
# Uncomment the following two lines and change base_dir to the root directory of local website folder
base_dir = "e:\\Users\\User\\Desktop\\uni\\dataMining\\datamining_p\\data-mining\\data\\www.ucl.ac.uk\\isd"
parse_and_index(base_dir)


# 2. Search query
results = search("Password reset")

# Simply print search results
for i, result in enumerate(results):
    print(i+1, '\n', result)








