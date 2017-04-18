import argparse

import searching
import time
from utils import check_python_version

SEARCH_LIMIT = 1000000
DISPLAY_LIMIT = 10

se = searching.SearchEngine()


def clamp(val, min_val, max_val):
    return max(min(val, max_val), min_val)


def print_search_results_page(page_no, search_results):
    end = page_no * DISPLAY_LIMIT
    start = end - DISPLAY_LIMIT

    for rank, doc in enumerate(search_results):
        if rank in range(start, end):
            print("%d. %s" % (rank + 1, doc.url))


def is_valid_ranking(parser, ranking):
    if ranking not in se.rankings:
        parser.error(("Invalid ranking algorithm: %s. Avaialble ranking algorithms: %s" % (ranking, se.rankings)))
    else:
        return str(ranking)


check_python_version()


parser = argparse.ArgumentParser(description='Search and print results.')
parser.add_argument('ranking', metavar='RANKING', action='store', type=lambda ranking: is_valid_ranking(parser, ranking),
                    help='ranking algorithm')

args = parser.parse_args()

already_explained = False

while True:
    query = input('\nEnter search query:\n')
    start_time = time.time()
    search_results = se.search(query, limit=SEARCH_LIMIT, ranking=args.ranking)
    end_time = time.time()
    time_taken = end_time - start_time
    no_of_results = len(search_results)

    if not no_of_results:
        print('\nYour search did not match any documents ({:.3f} seconds)'.format(time_taken))
    else:
        print('\nFound {} results ({:.3f} seconds)\n'.format(no_of_results, time_taken))
        total_pages = int(no_of_results / DISPLAY_LIMIT) + 1
        page = 1
        print_search_results_page(page, search_results)

        while True:
            if already_explained:
                key = input()
            else:
                key = input('\nEnter n or p for next or previous page, any other key to search again\n')
                already_explained = True

            if key == 'n':
                page += 1
                page = clamp(page, 1, total_pages)
                print_search_results_page(page, search_results)
            elif key == 'p':
                page -= 1
                page = clamp(page, 1, total_pages)
                print_search_results_page(page, search_results)
            else:
                break

