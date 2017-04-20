from __future__ import division
from utils import check_python_version
from evaluate_rankings import normalised_discounted_cumulative_gain
import sys

DELIMITER = ',###,'

check_python_version()

eval_file_path = sys.argv[1]

search_eval_file = open(eval_file_path, 'r')

headers = search_eval_file.readline()  # ignore headers

ndcgs = []

for line in search_eval_file:
    split_line = line.strip().split(DELIMITER)
    query = split_line[0]
    relevancies_string = split_line[2]
    relevancies = list(map(int, relevancies_string.split(',')))
    if -1 in relevancies:
        continue
    indexes = range(1, 11)
    ndcg = normalised_discounted_cumulative_gain(indexes, relevancies)
    ndcgs.append(ndcg)
    print(str(ndcg)+'\t'+query)

avg_ndcg = sum(ndcgs) / len(ndcgs)
print('Avg ndcg for '+eval_file_path.split('.csv')[0]+' : '+str(avg_ndcg))
