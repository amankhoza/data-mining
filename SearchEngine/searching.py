import logging
import os

from whoosh import index
from whoosh import scoring
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, ID, TEXT, KEYWORD
from whoosh.qparser import QueryParser

from SearchEngine.parsing import Document

logger = logging.getLogger(__name__)

INDEX_BASE_DIR = "index"


schema = Schema(url=ID(stored=True),
                path=ID(stored=True),
                title=TEXT(stored=True),
                description=TEXT(stored=True),
                content=TEXT(analyzer=StemmingAnalyzer()),
                keywords=KEYWORD)


def index_docs(docs):
    if not os.path.isdir(INDEX_BASE_DIR):
        os.mkdir(INDEX_BASE_DIR)
    ix = index.create_in(INDEX_BASE_DIR, schema=schema)
    writer = ix.writer()
    for doc in docs:
        writer.add_document(url=doc.url,
                            path=doc.path,
                            title=doc.title,
                            description=doc.description,
                            keywords=doc.keywords,
                            content=doc.content)
    writer.commit()


def search(query, limit=10, ranking_algorithm="BM25"):
    """Returns a list of sorted Document based on query"""
    logger.info("Received search request: Query: %s\tLimit: %d", query, limit)

    if ranking_algorithm == "BM25":
        scoring_method = scoring.BM25F()
    elif ranking_algorithm == "TF_IDF":
        scoring_method = scoring.TF_IDF()
    else:
        raise ValueError("ranking_algorithm must be 'BM25' or 'TF_IDF'")

    ix = index.open_dir(INDEX_BASE_DIR)

    qp = QueryParser("content", schema=ix.schema)
    q = qp.parse(query)

    docs = []

    with ix.searcher(weighting=scoring_method) as s:
        results = s.search(q, limit=limit)
        logger.info("\tMatched docs: %d", len(results))
        logger.info("\tScored docs: %d", results.scored_length())

        for result in results:
            docs.append(Document(**result.fields()))
    return docs
