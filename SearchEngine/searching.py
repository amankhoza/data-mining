import logging
import os
from parsing import Document
from utils import profile, MSG_START, MSG_SUCCESS, MSG_FAILED, print_progress, log_prof_data
from multiprocessing import cpu_count
logger = logging.getLogger(__name__)

try:
    from whoosh import index
    from whoosh import scoring
    from whoosh import sorting
    from whoosh.analysis import StemmingAnalyzer
    from whoosh.fields import Schema, ID, TEXT, KEYWORD, NUMERIC
    from whoosh.qparser import QueryParser
    from whoosh.qparser import MultifieldParser
except ImportError as e:
    logger.error('Error: %s.\n%s\n%s', str(e), 'whoosh must be installed to proceed.', 'Command to install missing library: pip install whoosh')
    exit(1)

INDEX_BASE_DIR = "index/"


stemming_analyzer = StemmingAnalyzer(cachesize=-1)
schema = Schema(url=ID(stored=True, unique=True),
                path=ID(stored=True, unique=True),
                title=TEXT(stored=True, analyzer=stemming_analyzer),
                description=TEXT(stored=True, analyzer=stemming_analyzer),
                keywords=KEYWORD(stored=True, analyzer=stemming_analyzer),
                links_in_keywords=KEYWORD(stored=True, analyzer=stemming_analyzer),
                content=TEXT(analyzer=stemming_analyzer),
                pagerank=NUMERIC(stored=True, sortable=True))


def index_docs(docs):
    index_documents(docs)
    log_prof_data(logger)


@profile
def index_documents(docs):
    msg = "Indexing documents"
    logger.info('%s %s', MSG_START, msg)
    try:

        if not os.path.isdir(INDEX_BASE_DIR):
            logger.info('Index directory does not exist. Trying to create directory.')
            try:
                os.mkdir(INDEX_BASE_DIR)
                logger.info('Directory created successfully.')
            except Exception as e:
                raise Exception('Failed to create directory for index: ' + str(e))

        ix = index.create_in(INDEX_BASE_DIR, schema=schema)
        writer = ix.writer(limitmb=256, procs=cpu_count(), multisegment=True)
        total_docs = len(docs)
        for i, doc in enumerate(docs):
            print_progress(i + 1, total_docs, 'Indexed', 'documents.')
            writer.add_document(url=doc.url,
                                path=doc.path,
                                title=doc.title,
                                keywords=doc.keywords,
                                links_in_keywords=doc.links_in_keywords,
                                description=doc.description,
                                content=doc.content,
                                pagerank=doc.pagerank)

        logger.info('%s Writing index to file', MSG_START)
        writer.commit(optimize=True)
        logger.info('%s Writing index to file', MSG_SUCCESS)
        logger.info('%s %s', MSG_SUCCESS, msg)
    except Exception as e:
        logger.warning('%s', e)
        logger.warning('%s %s', MSG_FAILED, msg)


class SearchEngine(object):
    FREQUENCY = 'frequency'
    BM25 = 'bm25'
    TF_IDF = 'tf_idf'
    DFREE = 'dfree'
    PL2 = 'pl2'
    PAGERANK = 'pagerank'
    CUSTOM = 'custom'

    def __init__(self):
        try:
            self.ix = index.open_dir(INDEX_BASE_DIR)
        except Exception as e:
            logger.error("Could not open index file: %s" % e)
            logger.info("To be able to search, an index has to be created first. Use index_website.py to create the index.")
            raise e

        self.scorers_dict = {
            SearchEngine.FREQUENCY: scoring.Frequency(),
            SearchEngine.BM25: scoring.BM25F(),
            SearchEngine.TF_IDF: scoring.TF_IDF,
            SearchEngine.DFREE: scoring.DFree,
            SearchEngine.PL2: scoring.PL2,
            SearchEngine.PAGERANK: scoring.Frequency,
            # Change the scoring with the custom scoring, once implemented
            SearchEngine.CUSTOM: scoring.Frequency}

        self.rankings = self.scorers_dict.keys()
        self.qp = MultifieldParser(
            ["title", "description", "keywords", "content"],
            schema=schema)
        self.qp_custom = MultifieldParser(
            ["title", "description", "keywords", "links_in_keywords", "content"],
            schema=schema,
            fieldboosts={"title": 10.0, "description": 1.0, "keywords": 1.0, "links_in_keywords": 1.0, "content": 1.0}
        )

    def search(self, query, limit=10, ranking=BM25):
        """Returns a list of sorted Document based on query"""
        logger.info("Received search request: Query: %s | Limit: %d | Ranking: %s", query, limit, ranking)

        try:
            scoring_method = self.scorers_dict[ranking]
        except KeyError:
            logger.error("Invalid ranking: %s", ranking)
            raise ValueError("Ranking must be one of these: %s", ', '.join(self.rankings))

        docs = []

        with self.ix.searcher(weighting=scoring_method) as s:
            # results = s.search(q, limit=limit)
            if ranking == SearchEngine.CUSTOM:
                q = self.qp_custom.parse(query)
                results = s.search(q, limit=limit)
            elif ranking == SearchEngine.PAGERANK:
                # Sort results by pagerank
                q = self.qp.parse(query)
                pagerank_facet = sorting.StoredFieldFacet('pagerank')
                results = s.search(q, limit=limit, sortedby=pagerank_facet, reverse=True)
            else:
                q = self.qp.parse(query)
                results = s.search(q, limit=limit)

            logger.info("\tMatched docs: %d", len(results))
            logger.info("\tScored docs: %d", results.scored_length())

            for result in results:
                docs.append(Document(**result.fields()))
        return docs
