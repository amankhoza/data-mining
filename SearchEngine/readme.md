
# Dependencies
In order to run the code in this project, you need python 3 installed with the following dependencies met:

* BeautifulSoup: `pip install beautifulsoup4`

* Whoosh: `pip install whoosh`

* lxml: `pip install lxml`

# Description

The project is split into two main components: `parsing` and `searching`.

1. `parsing` 

   This module is responsible for parsing/converting html files into `Document` objects. A `Document` object has fields like 'url', 'title', 'content' which are required by the indexing algorithm. In adition, `parsing` also computes other useful details, like document pagernak, and attaches these details to the each document. 

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
     * `ranking`: the ranking algorithms to use for ranking the results; three ranking algorithms are currently supported: `bm25`, `tf_idf` and `pagerank`.

   A searching example can be seen in [example_search.py](example_search.py).

3. User Search

   To search like a regular search engine run the run_search_engine script and pass in the ranking algorithm you wish to use as a command line argument:

   E.g. `python run_search_engine.py bm25`