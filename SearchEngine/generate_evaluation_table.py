import searching
from utils import check_python_version

SEARCH_LIMIT = 10
DISPLAY_LIMIT = 10

algorithms = ['bm25', 'tf_idf', 'pagerank']
queries = ['exam timetable', 'MEng Computer Science programme', 'syllabus', 'UCL societies', 'MEng entry requirements',
           'BSc entry requirements', 'UCL computer science (should direct to home page)', 'BSc Computer Science programme',
           'password change', 'unix', 'David Barber', 'Graham Roberts', 'how to change the cs account password', 'UCL servers',
           'java virtual machine', 'programming', 'moodle', 'lecturecast', 'exam locations', 'research projects', 'about UCL CS',
           'data mining', 'UCL courses', 'networking', 'COMPM012', 'undergraduate programme', 'postgraduate programme', 'grades',
           'provisional results', 'graduation date', 'graduation ceremony', 'graduation location', 'illness circumstances',
           'failing circumstances', 'what do my grades mean?', 'UCL teaching', 'tech society', 'year abroad', 'alumni',
           'online resources', 'turnitin', 'databases slides', 'holiday schedule', 'final grades', 'assessment', 'privacy',
           'safety measures', 'how to host a web page on a UCL server', 'coursework deadline policy', 'late submission']

check_python_version()

store = {}

for query in queries:

    store[query] = {}

    for algo in algorithms:

        search_results = searching.search(query, limit=SEARCH_LIMIT, ranking=algo)

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

out = open('table.csv', 'w')
out.write(headers+'\n')

# example headers
# query,url,title,description,relevance,index_bm25,index_tf_idf,index_pagerank

# print(store)

for query in store:
    first_query_flag = True
    for url in store[query]:
        title = store[query][url]['title']
        desc = store[query][url]['desc']
        if first_query_flag:
            query_string = query
            first_query_flag = False
        else:
            query_string = ''
        out.write('"{}","{}","{}","{}",'.format(query_string, url, title, desc))
        for algo in algorithms:
            algo_index = store[query][url][algo]
            out.write(',{}'.format(algo_index))
        out.write('\n')

out.flush()
out.close()
