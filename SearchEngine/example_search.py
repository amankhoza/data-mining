import os

import logging.config

import searching
from utils import check_python_version

check_python_version()


def config_logging():
    # Create directory to store logs in
    if not os.path.isdir("log"):
        os.mkdir('log')
    # Load basic logging configuration from file
    logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)

config_logging()

# query = "david barber"
# query = "about ucl cs"
# query = "exam timetable"
# query = "postgraduate programme"
# query = "provisional results"
query = "ucl home"

se = searching.SearchEngine()
search_results = se.search(query, limit=10, ranking=searching.SearchEngine.CUSTOM)

print('Total results: %d' % len(search_results))
for rank, doc in enumerate(search_results):
    print("%d. %s" % (rank + 1, doc.url))
