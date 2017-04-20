
# Dependencies
In order to run the code in this project, python 3 is required. In addition, the following python 3 libraries must be installed:

* BeautifulSoup 4.5.3: `pip install beautifulsoup4`

* Whoosh 2.7.4: `pip install whoosh`

* lxml 3.7.3: `pip install lxml`

# Description

The project is split into two main components: `parsing` and `searching`.

1. `parsing` 

   This module is responsible for parsing/converting html files into `Document` objects. A `Document` object has fields like 'url', 'title', 'content' which are required by the indexing algorithm. In adition, the `parsing` module also has functions for computing pageranks and adding these to each document.

2. `searching` 

   This module is responsible for creating the index and searching.

# How to use

First of all, make sure that the required dependencies are installed.

1. Indexing

   To index a website, run the [index_website.py](index_website.py) script from the terminal or command line. The website directory (local path) should be passed as an argument.
   
   **NOTE**: When the indexer is ran, the old index files (if present) will be deleted!

   E.g. `python index_website.py "/path/to/website/directory/"`

2. Programmatic Search

   To search the indexed website, use the `searching.search()` function. This function takes in 3 arguments:

     * `query`: the query to search for (e.g. "course syllabus")
     * `limit`: the number of desired search results
     * `ranking`: the ranking algorithm to use for ranking the results; multiple ranking algorithms are currently supported: `frequency`, `bm25`, `tf_idf`, `pagerank`, `pl2`, `custom` (a custom ranking algorithm that uses multiple metrics to compute rank, including bm25 and pagerank scores).

   A searching example can be seen in [example_search.py](example_search.py).

3. User Search

   To search like a regular search engine run the run_search_engine script and pass in the ranking algorithm you wish to use as a command line argument:

   E.g. `python run_search_engine.py bm25`