import logging
import os
import shutil
from pprint import pprint

import math
from whoosh.compat import iteritems
from whoosh.scoring import WeightingModel

from parsing import Document
from utils import profile, MSG_START, MSG_SUCCESS, MSG_FAILED, print_progress, log_prof_data
from multiprocessing import cpu_count
logger = logging.getLogger(__name__)

try:
    from whoosh import index
    from whoosh import scoring
    from whoosh import sorting
    from whoosh.analysis import StemmingAnalyzer, StandardAnalyzer
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
                title=TEXT(stored=True),
                title_stem=TEXT(analyzer=stemming_analyzer),
                description=TEXT(),
                description_stem=TEXT(analyzer=stemming_analyzer),
                keywords=KEYWORD(),
                keywords_stem=KEYWORD(analyzer=stemming_analyzer),
                links_in_keywords=KEYWORD(),
                links_in_keywords_stem=KEYWORD(analyzer=stemming_analyzer),
                content=TEXT(),
                content_stem=TEXT(analyzer=stemming_analyzer),
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

        else:
            logger.info('Index directory found. Deleting old index files...')
            for file in os.listdir(INDEX_BASE_DIR):
                file_path = os.path.join(INDEX_BASE_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    raise Exception('Failed to remove old index files: ' + str(e))
            logger.info('Old index files deleted successfully.')

        ix = index.create_in(INDEX_BASE_DIR, schema=schema)
        writer = ix.writer(limitmb=256, procs=cpu_count(), multisegment=True)
        total_docs = len(docs)
        for i, doc in enumerate(docs):
            print_progress(i + 1, total_docs, 'Indexed', 'documents.')
            writer.add_document(url=doc.url,
                                path=doc.path,
                                title=doc.title,
                                title_stem=doc.title,
                                keywords=doc.keywords,
                                keywords_stem=doc.keywords,
                                links_in_keywords=doc.links_in_keywords,
                                links_in_keywords_stem=doc.links_in_keywords,
                                description=doc.description,
                                description_stem=doc.description,
                                content=doc.content,
                                content_stem=doc.content,
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
            SearchEngine.TF_IDF: scoring.TF_IDF(),
            SearchEngine.PL2: scoring.PL2(),
            SearchEngine.PAGERANK: scoring.Frequency(),
            # Change the scoring with the custom scoring, once implemented
            SearchEngine.CUSTOM: scoring.MultiWeighting(
                default=scoring.BM25F(),
                # content=scoring.PL2(),
                # content_stem=scoring.PL2()
            )}

        self.rankings = self.scorers_dict.keys()
        self.qp = MultifieldParser(
            ["title_stem", "description_stem", "keywords_stem", "content_stem"],
            schema=schema)

        recall = 1
        precision = 2
        fieldboosts={"title": 2.0, "description": 1.3, "keywords": 1.5, "links_in_keywords": 1.5, "content": 1.0,
                     "title_stem": 1.2, "description_stem": 1.1, "keywords_stem": 1.2, "links_in_keywords_stem": 1.1, "content_stem": 1.0}

        total_standard = sum([value for key, value in fieldboosts.items() if not key.endswith('_stem')])
        total_stem = sum([value for key, value in fieldboosts.items() if key.endswith('_stem')])

        for key, value in fieldboosts.items():
            if key.endswith('_stem'):
                fieldboosts[key] = (fieldboosts[key] / total_stem) * (recall / (recall + precision))
            else:
                fieldboosts[key] = (fieldboosts[key] / total_standard) * (precision / (recall + precision))

        self.qp_custom = MultifieldParser(
            ["title", "description", "keywords", "links_in_keywords", "content",
             "title_stem", "description_stem", "keywords_stem", "links_in_keywords_stem", "content_stem"],
            schema=schema,
            fieldboosts=fieldboosts
        )

    def search(self, query, limit=10, ranking=CUSTOM):
        """Returns a list of sorted Document based on query"""
        logger.info("Received search request: Query: %s | Limit: %d | Ranking: %s", query, limit, ranking)

        try:
            scoring_method = self.scorers_dict[ranking]
        except KeyError:
            logger.error("Invalid ranking: %s", ranking)
            raise ValueError("Ranking must be one of these: %s", ', '.join(self.rankings))

        docs = []

        with self.ix.searcher(weighting=scoring_method) as s:
            if ranking == SearchEngine.CUSTOM:
                q = self.qp_custom.parse(query)
                results = s.search(q, limit=max(limit, 100))

                if not results.is_empty():
                    # max_score = max([r.score for r in results])
                    max_pagerank = math.log10(max([r.fields()["pagerank"] for r in results]) + 1)
                    result_list = []
                    for result in results:
                        fields = result.fields()
                        # result.score = result.score/max_score
                        pagerank_normalised = math.log10(fields["pagerank"] + 1) / max_pagerank
                        result.score = 0.6 * result.score + 0.4 * pagerank_normalised
                        result_list.append(result)
                    result_list.sort(key=lambda x: x.score, reverse=True)
                    for i, result in enumerate(result_list[:limit]):
                        doc = Document(**result.fields())
                        docs.append(doc)
                        # print(str(i) + ". ", doc.url, result.score, result.rank, result.combined, doc.pagerank)
                    return docs
            else:
                facet = None
                reverse = False
                q = self.qp.parse(query)

                if ranking == SearchEngine.PAGERANK:
                    reverse = True
                    facet = sorting.StoredFieldFacet('pagerank')

                results = s.search(q, limit=limit, sortedby=facet, reverse=reverse)

                logger.info("\tMatched docs: %d", len(results))
                logger.info("\tScored docs: %d", results.scored_length())

                for result in results:
                    docs.append(Document(**result.fields()))
        return docs
