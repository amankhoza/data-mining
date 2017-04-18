import os

from searching import SearchEngine
from utils import check_python_version, process_batch, read_csv, write_csv

check_python_version()

algorithms = [SearchEngine.BM25, SearchEngine.TF_IDF, SearchEngine.PAGERANK]
queries = ['exam timetable', 'MEng Computer Science programme', 'syllabus', 'UCL societies', 'MEng entry requirements',
           'BSc entry requirements', 'UCL computer science (should direct to home page)', 'BSc Computer Science programme',
           'password change', 'unix', 'David Barber', 'Graham Roberts', 'how to change the cs account password', 'UCL servers',
           'java virtual machine', 'programming', 'moodle', 'lecturecast', 'exam locations', 'research projects', 'about UCL CS',
           'data mining', 'UCL courses', 'networking', 'COMPM012', 'undergraduate programme', 'postgraduate programme', 'grades',
           'provisional results', 'graduation date', 'graduation ceremony', 'graduation location', 'illness circumstances',
           'failing circumstances', 'what do my grades mean?', 'UCL teaching', 'tech society', 'year abroad', 'alumni',
           'online resources', 'turnitin', 'databases slides', 'holiday schedule', 'final grades', 'assessment', 'privacy',
           'safety measures', 'how to host a web page on a UCL server', 'coursework deadline policy', 'late submission']

headers = ['query', 'url', 'relevance']
relevances_file = 'relevances.csv'

SEARCH_LIMIT = 10

se = SearchEngine()


# Useful for multithreaded implementation; also adds relevances to documents
def search_wrapper(query, SEARCH_LIMIT, ranking, relevances):
    results = se.search(query, SEARCH_LIMIT, ranking)
    results_with_relevances = []
    for result in results:
        relevance = -1
        if (query, result.url) in relevances:
            relevance = relevances[(query, result.url)]
        results_with_relevances.append((result, relevance))
    return query, ranking, results_with_relevances


def get_search_results_with_relevances():
    user_relevances = {}
    # Read user relevances from csv
    if os.path.isfile(relevances_file):
        user_relevances = {(row[0], row[1]): row[2] for row in read_csv(filename=relevances_file, skip_headers=True)}

    print("Generating search results...")
    # document list with relevances (search results) for each (query, algorithm) pair
    results = {
        (query, algo): results
        for query, algo, results in process_batch(
        [
            (query, SEARCH_LIMIT, algo, user_relevances)
            for query in queries for algo in algorithms
            ],
        search_wrapper
    )
        }
    return results


def update_relevances(results):
    # list of unique (query, url) pairs
    relevances = set([(query, doc.url, relevance) for (query, algo), docs_with_relevance in results.items() for doc, relevance in docs_with_relevance])

    print("Total results: %d" % len([doc for (query, algo), docs in results.items() for doc in docs]))
    print("Total unique results: %d" % len(relevances))

    write_csv(sorted(relevances, key=lambda x: (x[0].lower(), x[1])), filename=relevances_file, headers=headers)


# This check is required for multithreaded implementation
if __name__ == "__main__":
    results_with_relevances = get_search_results_with_relevances()
    update_relevances(results_with_relevances)
