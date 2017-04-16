import sys
import os

'''
Simple text based ranking, uses Python 2
'''


def progress(count, total, status='Complete'):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s %s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def rankUrls(searchTerm):
    htmlFilePaths = []
    rankings = []
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if name.endswith('.html'):
                path = os.path.join(root, name)
                htmlFilePaths.append(path)

    i = 1
    n = len(htmlFilePaths)

    for filePath in htmlFilePaths:
        progress(i, n, str(i)+'/'+str(n))
        i += 1
        occurances = 0
        fileHandle = open(filePath, 'r')
        fileContents = fileHandle.read()
        occurances += fileContents.count(searchTerm)
        fileHandle.close()
        if occurances != 0:
            rankings.append((occurances, filePath))

    return sorted(rankings, reverse=True)


def displayResults(rankedUrls):
    if not rankedUrls:
        print('\nNo search results found')
    else:
        print('\nTop 10 search results:')
    for rankedUrl in rankedUrls[:10]:
        rank = rankedUrl[0]
        url = rankedUrl[1]
        print('{}\t{}'.format(rank, url))


os.system('reset')  # clear terminal

directory = sys.argv[1]

while True:
    searchTerm = raw_input('\nEnter search term:\n')
    rankedUrls = rankUrls(searchTerm)
    displayResults(rankedUrls)
