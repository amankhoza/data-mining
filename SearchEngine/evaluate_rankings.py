from __future__ import division
import os
from searching import SearchEngine
from utils import check_python_version, process_batch, read_csv, write_csv
from math import log

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
relevancies_file = 'user_relevancies.csv'

SEARCH_LIMIT = 10

se = SearchEngine()


# Useful for multithreaded implementation; also adds relevances to documents
def search_wrapper(query, SEARCH_LIMIT, ranking, relevancies):
    results = se.search(query, SEARCH_LIMIT, ranking)
    results_with_relevancies = []
    for result in results:
        relevance = -1
        if (query, result.url) in relevancies:
            relevance = relevancies[(query, result.url)]
        results_with_relevancies.append((result, relevance))
    return query, ranking, results_with_relevancies


def get_user_relevancies(file):
    user_relevancies = {}
    # Read user relevances from csv
    if os.path.isfile(relevancies_file):
        for row in read_csv(filename=file, skip_headers=True):
            try:
                relevance = int(row[2])
            except ValueError:
                relevance = -1
            user_relevancies[(row[0], row[1])] = relevance
    return user_relevancies


def get_search_results_with_relevancies(user_relevancies=None):
    if user_relevancies is None:
        user_relevancies = {}

    print("Generating search results...")
    # document list with relevances (search results) for each (query, algorithm) pair
    results = {
        (query, algo): results
        for query, algo, results in process_batch(
        [
            (query, SEARCH_LIMIT, algo, user_relevancies)
            for query in queries for algo in algorithms
            ],
        search_wrapper
    )
        }
    return results


def update_relevancies(results, user_relevancies=None):

    if user_relevancies is None:
        user_relevancies = {}

    # list of unique (query, url) pairs
    relevancies = {(query, doc.url): relevance for (query, algo), docs_with_relevance in results.items() for doc, relevance in docs_with_relevance}

    user_relevancies = {(query, url):relevance for (query, url),relevance in user_relevancies.items() if relevance > -1}

    for query_url_pair, relevance in relevancies.items():
        if query_url_pair not in user_relevancies:
            user_relevancies[query_url_pair] = relevance

    final_relevancies = [(query, url, relevance) for (query, url), relevance in user_relevancies.items()]

    write_csv(sorted(final_relevancies, key=lambda x: (x[0].lower(), x[1])), filename=relevancies_file, headers=headers)


def sort_by_index(index_relevance):
    return sorted(index_relevance, key=lambda x: x[0])


def rel_log(index, relevance):
    return relevance / log(index + 1, 2.0)


def cumulative_gain(relevances):
    return sum(relevances)


def discounted_cumulative_gain(indexes, relevances):
    n = len(indexes)
    dcg = 0
    for i in range(0, n):
        dcg += rel_log(indexes[i], relevances[i])
    return dcg


def sort_relevances(relevances):
    return sorted(relevances, reverse=True)


def ideal_discounted_cumulative_gain(indexes, relevances):
    sorted_relevances = sort_relevances(relevances)
    idcg = discounted_cumulative_gain(indexes, sorted_relevances)
    return idcg


def normalised_discounted_cumulative_gain(indexes, relevances):
    dcg = discounted_cumulative_gain(indexes, relevances)
    idcg = ideal_discounted_cumulative_gain(indexes, relevances)
    if dcg>0 and idcg>0:
        return dcg / idcg
    else:
        return 0


# This check is required for multithreaded implementation
if __name__ == "__main__":
    # Read user relevancies from file
    user_relevancies = get_user_relevancies(relevancies_file)

    # Get search results and add the relevancies to each document
    results_with_relevancies = get_search_results_with_relevancies(user_relevancies)

    evaluation_results = {}

    for (query, algo) in results_with_relevancies:
        indexes = range(1, len(results_with_relevancies[(query, algo)])+1)
        relevances = [r for doc, r in results_with_relevancies[(query, algo)]]
        ndcg = normalised_discounted_cumulative_gain(indexes, relevances)
        if query not in evaluation_results:
            evaluation_results[query] = {}
        evaluation_results[query][algo] = ndcg

    for q in sorted(evaluation_results, key=lambda x: x[0]):
        print(q, evaluation_results[q])

    # Update the user relevancies file with the new results
    update_relevancies(results_with_relevancies, user_relevancies)
