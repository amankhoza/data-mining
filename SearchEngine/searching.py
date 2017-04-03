import logging
import os

from whoosh import index
from whoosh import scoring
from whoosh import sorting
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, ID, TEXT, KEYWORD, NUMERIC
from whoosh.qparser import QueryParser

from parsing import Document
from utils import profile, MSG_START, MSG_SUCCESS, MSG_FAILED, print_progress, log_prof_data

logger = logging.getLogger(__name__)

INDEX_BASE_DIR = "index"


schema = Schema(url=ID(stored=True),
                path=ID(stored=True),
                title=TEXT(stored=True),
                description=TEXT(stored=True),
                keywords=KEYWORD,
                links_in_keywords=KEYWORD(stored=True),
                content=TEXT(analyzer=StemmingAnalyzer()),
                pagerank=NUMERIC(stored=True, sortable=True))


def index_docs(docs):
    index_documents(docs)
    log_prof_data()


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
                raise Exception('Failed to create directory for index: ' + e)

        ix = index.create_in(INDEX_BASE_DIR, schema=schema)
        writer = ix.writer()
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
        writer.commit()
        logger.info('%s Writing index to file', MSG_SUCCESS)
        logger.info('%s %s', MSG_SUCCESS, msg)
    except Exception as e:
        logger.warning('%s', e)
        logger.warning('%s %s', MSG_FAILED, msg)


def search(query, limit=10, ranking="BM25"):
    """Returns a list of sorted Document based on query"""
    logger.info("Received search request: Query: %s\tLimit: %d\tRanking: %s", query, limit, ranking)

    if ranking == "bm25":
        scoring_method = scoring.BM25F()
    elif ranking == "tf_idf":
        scoring_method = scoring.TF_IDF()

    elif ranking == "pagerank":
        scoring_method = scoring.BM25F
    else:
        raise ValueError("ranking must be one of these: 'bm25', 'tf_idf', 'pagerank")

    try:
        ix = index.open_dir(INDEX_BASE_DIR)
    except Exception as e:
        print("Could not open index file: %s" % e)
        print("To be able to search, an index has to be created first. Use index_website.py to create the index.")
        exit()

    qp = QueryParser("content", schema=ix.schema)
    q = qp.parse(query)

    docs = []

    with ix.searcher(weighting=scoring_method) as s:
        # results = s.search(q, limit=limit)
        if ranking == 'pagerank':
            pagerank_facet = sorting.StoredFieldFacet('pagerank')
            results = s.search(q, limit=limit, sortedby=pagerank_facet, reverse=True)
        else:
            results = s.search(q, limit=limit)

        logger.info("\tMatched docs: %d", len(results))
        logger.info("\tScored docs: %d", results.scored_length())

        for result in results:
            docs.append(Document(**result.fields()))
    return docs
