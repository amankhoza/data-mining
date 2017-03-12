import urllib
from bs4 import BeautifulSoup


def rankUrls(searchTerm, urls):
    rankings = []
    for url in urls:
        occurances = 0
        web_page = urllib.request.urlopen(url)
        soup = BeautifulSoup(web_page, 'lxml')
        for body in soup.findAll('body'):
            occurances += str(body).count(searchTerm)
        rankings.append((occurances, url))
    return sorted(rankings, reverse=True)


def displayResults(rankedUrls):
    print('\nSearch results:')
    for rankedUrl in rankedUrls:
        rank = rankedUrl[0]
        url = rankedUrl[1]
        print('{}\t{}'.format(rank, url))


urls = []
urls.append('http://www.ucl.ac.uk/estates/roombooking/')
urls.append('https://www.ucl.ac.uk/staff/term-dates')
urls.append('http://www.ucl.ac.uk/about/why/rankings')
urls.append('http://www.ucl.ac.uk/prospective-students/undergraduate/application')
urls.append('https://aoc.ucl.ac.uk/alumni')

while True:
    searchTerm = input('\nEnter search term:\n')
    rankedUrls = rankUrls(searchTerm, urls)
    displayResults(rankedUrls)
