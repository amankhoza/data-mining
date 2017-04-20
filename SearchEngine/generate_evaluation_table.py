from searching import SearchEngine
from utils import check_python_version
import pandas as pd

SEARCH_LIMIT = 10
DISPLAY_LIMIT = 10

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


def get_relevance(query, url):
    relevance_df = relevances_df[(relevances_df['query']==query) & (relevances_df['url']==url)]
    return int(relevance_df['relevance'].values[0])


check_python_version()

store = {}

relevances_df = pd.read_csv('user_relevancies.csv')

se = SearchEngine()

for query in queries:

    store[query] = {}

    for algo in algorithms:

        search_results = se.search(query, limit=SEARCH_LIMIT, ranking=algo)

        for rank, doc in enumerate(search_results):

            url = doc.url

            if url not in store[query]:
                store[query][url] = {}
                store[query][url]['title'] = doc.title
                store[query][url]['desc'] = doc.description
                for i in algorithms:
                    store[query][url][i] = 0

            store[query][url][algo] = rank+1

headers = 'query,url,title,description,relevance'
for algo in algorithms:
    headers = headers+',index_'+algo

out = open('table.csv', 'w', encoding='utf8')
out.write(headers+'\n')

# example headers
# query,url,title,description,relevance,index_bm25,index_tf_idf,index_pagerank

for query in store:
    for url in store[query]:
        title = store[query][url]['title']
        desc = store[query][url]['desc']
        relevance = get_relevance(query, url)
        out.write('"{}","{}","{}","{}",{}'.format(query, url, title, desc, relevance))
        for algo in algorithms:
            algo_index = store[query][url][algo]
            out.write(',{}'.format(algo_index))
        out.write('\n')

out.flush()
out.close()
