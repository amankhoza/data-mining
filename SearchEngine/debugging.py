#!/usr/bin/python
import os
import sys

import logging.config

import parsing
import searching

# Configure logging
if not os.path.isdir("log"):
    os.mkdir('log')
logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)


def usage():
    print('Usage: debugging.py <webiste_directory>')


def get_directory_param():
    args = sys.argv[1:]

    if not len(args) == 1:
        print('No website_directory supplied!')
        usage()
        exit()

    dir = args[0]
    if not os.path.isdir(dir):
        print('Directory does not exist!')
        exit()
    return dir


def reset_pageranks(docs):
    for doc in docs:
        doc.pagerank = 1.0

def main():

    dir = get_directory_param()
    # Retrieve the parsed documents
    docs = parsing.UCLParser.parse_website(dir, use_cache=False, multithreading=True)

    # Recompute pagerank
    reset_pageranks(docs)
    parsing.UCLParser.add_pagerank(docs)

    # Sort documents by pagerank
    docs.sort(key=lambda doc: doc.pagerank, reverse=True)

    # Print documents pageranks
    for doc in docs:
        print(doc.url, doc.pagerank)



    return


if __name__ == "__main__":
    main()
