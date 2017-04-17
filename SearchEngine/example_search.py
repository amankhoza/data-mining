import searching
from utils import check_python_version

check_python_version()

query = "average salary after course"
search_results = searching.search(query, limit=50, ranking='bm25')

print('Total results: %d' % len(search_results))
for rank, doc in enumerate(search_results):
    print("%d. %s" % (rank + 1, doc.url))
