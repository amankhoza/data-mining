import logging
import os
import pickle
import re

from bs4 import BeautifulSoup
from bs4 import Comment

from utils import print_progress, profile, log_prof_data, MSG_START, MSG_SUCCESS, MSG_FAILED

logger = logging.getLogger(__name__)


class UCLParser(object):
    NO_INDEX_COMMENT = 'noindex'
    NO_INDEX_END_COMMENT = 'endnoindex'

    def __init__(self, **kwargs):
        self.PARSER = kwargs.get('parser', 'lxml')
        self.MIN_DATA_LEN = kwargs.get('min_data_len', 3000)

        self.local_path_to_url = None

    def parse(self, root_dir, cache=True):
        msg = "Parsing"
        logger.info('%s %s', MSG_START, msg)
        logger.info("Directory: %s", root_dir)

        pickle_file = re.sub('/|:|\\\\', '', root_dir) + '.pickle'
        try:
            with open(pickle_file, 'rb') as handle:
                docs = pickle.load(handle)
                logger.info("Loaded documents %d from cache.", len(docs))
        except Exception:
            files = UCLParser.get_files(root_dir, '.html')
            docs = self.parse_files(files)

            with open(pickle_file, 'wb') as handle:
                pickle.dump(docs, handle, protocol=pickle.HIGHEST_PROTOCOL)

        UCLParser.validate_links_out(docs)
        docs = UCLParser.add_links_in(docs)

        UCLParser.add_pagerank(docs)

        log_prof_data()
        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @profile
    def parse_files(self, files):
        msg = "Parsing files"
        logger.info('%s %s', MSG_START, msg)

        docs = []
        total = len(files)
        logger.info('Found %d files.', total)

        for i, file in enumerate(files):
            print_progress(i + 1, total, 'Scanned', 'files.')
            doc = self.parse_file(file)
            if doc:
                docs.append(doc)

        logger.info('Successfully parsed %d documents', len(docs))
        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @profile
    def parse_file(self, file_path_abs):
        msg = "Parsing file "
        logger.debug('%s %s', MSG_START, msg)
        logger.debug("Parsing %s", file_path_abs)

        doc = None

        try:
            # TODO: try auto detecting character encoding. chardet python library might be useful
            with open(file_path_abs, 'r', encoding='utf8') as f:
                data = f.read()

                soup = BeautifulSoup(data, self.PARSER)
                if UCLParser.check_soup(soup):
                    url = UCLParser.extract_url(data)

                    if url:
                        doc = Document(path=file_path_abs, url=url)
                        doc.title = UCLParser.extract_title(soup)
                        doc.description = UCLParser.extract_description(soup)
                        doc.keywords = UCLParser.extract_keywords(soup)
                        doc.links_out = UCLParser.extract_links_out(soup)

                        data = UCLParser.remove_no_index(data)
                        soup = BeautifulSoup(data, self.PARSER)
                        soup = UCLParser.clean_soup(soup)
                        doc.content = UCLParser.extract_content(soup)
                    else:
                        raise Exception("Url not found!")
                else:
                    raise Exception("Soup check failed!")

        except Exception as e:
            logger.debug("Ignoring file: %s", e)

        if doc:
            logger.debug('%s %s', MSG_SUCCESS, msg)
        else:
            logger.debug('%s %s', MSG_FAILED, msg)
        return doc

    @staticmethod
    def get_files(dir, extension=None):
        """ Returns a list of absolute paths of the files in dir and its subdirectories. """

        _files = []
        for subdir, dirs, files in os.walk(dir):
            for file in files:
                name, _extension = os.path.splitext(file)
                file_path_abs = os.path.join(subdir, file)
                if extension is None or _extension == extension:
                    _files.append(file_path_abs)
        return _files

    @staticmethod
    def check_soup(soup):
        div_elements = soup.findAll('div')
        if not div_elements or not (len(div_elements) > 2):
            logger.debug('Soup has less than 2 div elements!')
            return False

        head_elements = soup.findAll(['link', 'script', 'meta'])
        if not head_elements or not (len(head_elements) > 3):
            logger.debug('Soup has less than 3 link, scrip or meta elements!')
            return False

        return True

    @staticmethod
    def remove_no_index(data):
        msg = "Removing non indexable elements "
        logger.debug('%s %s', MSG_START, msg)

        data = re.sub('<!--' + UCLParser.NO_INDEX_COMMENT + '-->(?s).*?<!--' + UCLParser.NO_INDEX_END_COMMENT + '-->',
                      '', data)

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return data

    @staticmethod
    def clean_soup(soup):
        """Removes comments and style, script, br tags."""

        msg = "Cleaning soup "
        logger.debug('%s %s', MSG_START, msg)

        for element in soup.findAll(['br', 'script', 'style', 'iframe']):
            element.extract()

        # soup = self.remove_noindex_elements(soup)

        for comment in soup(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return soup

    @staticmethod
    def clean_text(text):
        # TODO: Improve this function if needed
        text = text.replace("&nbsp", " ")
        # text = re.sub(r'[^a-zA-Z0-9 ]',' ',text)
        text = re.sub('\s+', ' ', text).strip()
        # text = text.lower()
        return text

    @staticmethod
    def extract_url(data):
        msg = 'Extracting url'
        logger.debug('%s %s', MSG_START, msg)

        # url = \
        #     re.findall("(?<=<!-- Mirrored from )(.*)(?= by HTTrack Website Copier)",
        #                str(data))[0]
        url = re.search("(?<=<!-- Mirrored from )(.*)(?= by HTTrack Website Copier)", str(data)).group()
        if url:
            logger.debug("Url found: %s", url)
        else:
            url = None
            logger.debug("Url not found!")

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return url

    @staticmethod
    def extract_title(soup):
        msg = 'Extracting title '
        logger.debug('%s %s', MSG_START, msg)

        title = ""
        try:
            title = soup.find('title').find(text=True)
            title = UCLParser.clean_text(title)
        except Exception as e:
            logger.debug('Could not extract title!')

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return title

    @staticmethod
    def extract_description(soup):
        msg = 'Extracting description '
        logger.debug('%s %s', MSG_START, msg)
        desc = ''
        try:
            desc = soup.find('meta', attrs={"name": "description"})['content']
            # desc = clean_text(desc)
        except Exception as e:
            logger.debug("Could not extract description!")

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return desc

    @staticmethod
    def extract_keywords(soup):
        msg = 'Extracting keywords '
        logger.debug('%s %s', MSG_START, msg)

        keywords = ""

        try:
            keywords = soup.find('meta', attrs={"name": "keywords"})['content']
        except Exception as e:
            logger.debug("Could not extract keywords")

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return keywords

    @staticmethod
    def extract_content(soup):
        msg = 'Extracting content '
        logger.debug('%s %s', MSG_START, msg)

        content = ""

        try:
            text_elements = soup.find('body').findAll(text=True)
            text = ' '.join([str(element) for element in text_elements])
            content = UCLParser.clean_text(text)

        except Exception as e:
            logger.debug("Could not extract content")

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return content

    @staticmethod
    def extract_links_out(soup):
        msg = 'Extracting links_out'
        logger.debug('%s %s', MSG_START, msg)

        links = []
        try:
            a_elements = soup.find('body').findAll('a', href=True)

            for a_elem in a_elements:
                href = a_elem['href']
                text_elements = a_elem.findAll(text=True)
                text = ' '.join([str(element) for element in text_elements])
                links.append((href, UCLParser.clean_text(text)))

        except Exception as e:
            logger.debug("Could not extract links: %s", e)

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return links

    @staticmethod
    @profile
    def validate_links_out(docs):
        msg = "Validating document links_out"
        logger.info('%s %s', MSG_START, msg)

        path_to_url = {}
        for doc in docs:
            path_to_url[doc.path] = doc.url

        # url_to_path = {}
        # for doc in docs:
        #     url_to_path[doc.url] = doc.path
        # logger.info("Total unique urls: " + str(len(url_to_path.keys())))
        #
        urls = set()

        total_docs = len(docs)
        for i, doc in enumerate(docs):
            print_progress(i + 1, total_docs, 'Validated', 'documents.')
            dir = os.path.dirname(doc.path)
            links = []
            for link, text in doc.links_out:
                path = os.path.normpath(os.path.join(dir, link))
                if path not in path_to_url:
                    path = os.path.normpath(os.path.join(path, 'index.html'))
                try:
                    url = path_to_url[path]
                    links.append((url, text))
                    urls.add(url)
                except Exception as e:
                    # logger.info('Error: %s', e)
                    # logger.info('Link on: %s', doc.url)
                    # logger.info('Path not found: %s', path)
                    # URL Not found in local_path_to_url
                    pass
            doc.links_out = links

        logger.info('Validated unique urls: %d', len(urls))
        # for url in (url_to_path.keys() - urls):
        #     print('%s\n%s\n%s\n\n' % (url, url_to_path[url], path_to_url[url_to_path[url]]))
        logger.info('%s %s', MSG_SUCCESS, msg)

    @staticmethod
    @profile
    def add_links_in(docs):
        msg = 'Adding links_in'
        logger.info('%s %s', MSG_START, msg)

        docs_dict = {}
        for doc in docs:
            doc.links_in_keywords = set()
            docs_dict[doc.url] = doc

        for url, doc in docs_dict.items():
            for link, text in doc.links_out:
                try:
                    docs_dict[link].links_in.append((url, text))
                    docs_dict[link].links_in_keywords.add(text)
                except KeyError:
                    # this shouldn't happen
                    logger.error("Link not found: %s", link)
                    pass

        # print("Total docs: " + str(len(docs)))
        # docs = [doc for doc in docs if len(doc.links_in) > 0]
        # logger.info("Found docs with incoming links from other docs: %d", len(docs))

        for doc in docs:
            doc.links_in_keywords = ', '.join([keyword.replace(',', ' ') for keyword in doc.links_in_keywords])

        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @staticmethod
    @profile
    def add_pagerank(docs, epochs=30, damping_factor=0.85):
        msg = 'Computing document pageranks'
        logger.info('%s %s', MSG_START, msg)
        docs_dict = {doc.url: doc for doc in docs}

        total_epochs = epochs
        while epochs > 0:
            print_progress(total_epochs - epochs + 1, total_epochs, 'Epoch')
            for url, doc in docs_dict.items():
                interm = 0
                for link_url, link_text in doc.links_in:
                    doc_in = docs_dict[link_url]
                    interm += doc_in.pagerank / len(doc_in.links_out)
                doc.pagerank = (1-damping_factor) + damping_factor*interm
            epochs -= 1

        s = sum([doc.pagerank for doc in docs])
        print("Total docs: %d, Pagerank sum: %.f3" % (len(docs), s))

        logger.info('%s %s', MSG_SUCCESS, msg)

class Document(object):
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', None)
        self.url = kwargs.get('url', None)
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.keywords = kwargs.get('keywords', '')
        self.content = kwargs.get('content', '')
        self.links_out = kwargs.get('links_in', [])
        self.links_in = kwargs.get('links_out', [])
        self.links_in_keywords = kwargs.get('links_in_keywords', '')
        self.pagerank = kwargs.get('pagerank', 1)

    def __str__(self):
        return \
            "Path: {}\n" \
            "URL: {}\n" \
            "Title: {}\n" \
            "Description: {}\n" \
            "Keywords: {}\n" \
            "Content: {}\n" \
            "Links Out: {}\n" \
            "Links In: {}\n" \
            "Links In Keywords: {}\n" \
            "PageRank: {}\n".format(
                self.path,
                self.url,
                self.title,
                self.description,
                self.keywords,
                self.content,
                self.links_out,
                self.links_in,
                self.links_in_keywords,
                self.pagerank
            )
