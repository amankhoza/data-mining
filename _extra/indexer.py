import sys
import os
from bs4 import BeautifulSoup
from bs4 import Comment
from bs4 import Doctype


def progress(count, total, status='Complete'):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s %s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def getHTMLFilePaths(directory):
    htmlFilePaths = []
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if name.endswith('.html'):
                path = os.path.join(root, name)
                htmlFilePaths.append(path)
    return htmlFilePaths


def removeJunk(soup):
    comments = soup.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]  # remove comments
    [doctype.extract() for doctype in soup.contents if isinstance(doctype, Doctype)]  # remove doctypes
    [script.extract() for script in soup('script')]  # remove scripts


def extractTextFromHTML(soup):
    texts = soup.findAll(text=True)
    text = ' '.join([item.strip() for item in texts])
    return text


def extractLinksFromHTML(soup):
    links = soup.find_all('a', href=True)
    return [link['href'] for link in links]  # might need to tweak to remove mailtos


os.system('reset')  # clear terminal

directory = sys.argv[1]

filePaths = getHTMLFilePaths(directory)

i = 1
n = len(filePaths)

for filePath in filePaths:
    progress(i, n)
    i += 1

    file = open(filePath)
    soup = BeautifulSoup(file, 'lxml')

    removeJunk(soup)

    text = extractTextFromHTML(soup)
    links = extractLinksFromHTML(soup)

    # print(filePath)
    # print(text)
    # print(links)

    file.close()
