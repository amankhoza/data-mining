#!/usr/bin/python
import os
import sys

import logging.config

import parsing
import searching

if not os.path.isdir("log"):
    os.mkdir('log')
logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)


def usage():
    print('Usage: index_website.py <webiste_directory>')


def main():
    # print command line arguments

    args = sys.argv[1:]

    if not len(args) == 1:
        print('No website_directory supplied!')
        usage()
        return

    dir = args[0]
    if not os.path.isdir(dir):
        print('Directory does not exist!')
        return

    docs = parsing.UCLParser.parse_website(dir)

    searching.index_docs(docs)

    return


if __name__ == "__main__":
    main()
