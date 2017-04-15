#!/usr/bin/python
import argparse
import os
import sys

import logging.config
import logging.handlers
from itertools import accumulate
from logging import FileHandler

import datetime

import parsing
import searching


def config_logging(debug=False):
    # Create directory to store logs in
    if not os.path.isdir("log"):
        os.mkdir('log')

    # Load basic logging configuration from file
    logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)

    if debug:
        # Configure file handler for debugging
        current_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_handler = logging.handlers.RotatingFileHandler('log/indexing-' + current_date + '.log', mode='a')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)s:%(levelname)s:%(lineno)d:  %(message)s')
        file_handler.setFormatter(formatter)

        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(file_handler)


def is_valid_dir(parser, dir):
    if not os.path.isdir(dir):
        parser.error(("The directory %s does not exist!" % dir))
    else:
        return str(dir)


def main():
    parser = argparse.ArgumentParser(description='Parse html files and create an index.')
    parser.add_argument('-debug', action='store_const',
                        const=True, default=False,
                        help='debugging mode (creates detailed logs in log directory)')
    parser.add_argument('website_dir', metavar='WEBSITE_DIRECTORY', action='store', type=lambda dir: is_valid_dir(parser, dir),
                        help='path to directory containing website files')

    args = parser.parse_args()
    config_logging(args.debug)

    docs = parsing.UCLParser.parse_website(args.website_dir, multithreading=not args.debug)
    searching.index_docs(docs)

if __name__ == "__main__":
    main()
