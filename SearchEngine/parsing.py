
import logging
import os
import pickle
import re

from bs4 import BeautifulSoup
from bs4 import Comment

from utils import print_progress, profile, log_prof_data, MSG_START, MSG_SUCCESS, MSG_FAILED, get_files, process_batch


logger = logging.getLogger(__name__)
docs_cache_dir = 'docs_cache/'


class UCLParser(object):
    NO_INDEX_COMMENT = 'noindex'
    NO_INDEX_END_COMMENT = 'endnoindex'
    PARSER = 'lxml'

    @staticmethod
    @profile
    def parse_website(root_dir, use_cache=False):
        msg = "Parsing website"
        logger.info('%s %s', MSG_START, msg)
        logger.info("From directory %s", root_dir)

        pickle_file = docs_cache_dir + re.sub('/|:|\\\\', '', root_dir) + '.pickle'
        loaded_from_cache = False

        docs = []

        if use_cache:
            try:
                with open(pickle_file, 'rb') as handle:
                    docs = pickle.load(handle)
                    loaded_from_cache = True
                    logger.info("Loaded %d documents from cache.", len(docs))
            except Exception:
                logger.info("No cached documents found")

        if not loaded_from_cache:
            logger.info("Getting file paths...")
            files = get_files(root_dir, '.html')
            logger.info("Found %d html files", len(files))
            logger.info("Parsing files...")
            docs = [doc for doc in process_batch([(file,) for file in files], UCLParser.parse_file) if doc is not None]

            logger.info("Successfully parsed %d files", len(docs))

            docs = UCLParser.validate_docs_links_out(docs)
            UCLParser.remove_duplicate_docs(docs)
            docs = UCLParser.add_links_in(docs)

            UCLParser.add_pagerank(docs)

            if not os.path.isdir(docs_cache_dir):
                os.mkdir(docs_cache_dir)
            try:
                with open(pickle_file, 'wb') as handle:
                    pickle.dump(docs, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    logger.info("Successfully cached %d documents.", len(docs))
            except Exception as e:
                logger.info("Failed to cache documents: %s", e)

        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @staticmethod
    @profile
    def parse_file(file_path_abs):
        msg = "Parsing file "
        logger.debug('%s %s %s', MSG_START, msg, file_path_abs)

        doc = None

        try:
            # TODO: try auto detecting character encoding. chardet python library might be useful
            with open(file_path_abs, 'r', encoding='utf8') as f:
                data = f.read()

                soup = BeautifulSoup(data, UCLParser.PARSER)
                if UCLParser.check_soup(soup):
                    url = UCLParser.extract_url(data)

                    if url:
                        doc = Document(path=file_path_abs, url=url)
                        doc.title = UCLParser.extract_title(soup)
                        doc.description = UCLParser.extract_description(soup)
                        doc.keywords = UCLParser.extract_keywords(soup)
                        doc.links_out = UCLParser.extract_links_out(soup)

                        data = UCLParser.remove_no_index(data)
                        soup = BeautifulSoup(data, UCLParser.PARSER)
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
    @profile
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
    @profile
    def remove_no_index(data):
        msg = "Removing non indexable elements "
        logger.debug('%s %s', MSG_START, msg)

        data = re.sub('<!--' + UCLParser.NO_INDEX_COMMENT + '-->(?s).*?<!--' + UCLParser.NO_INDEX_END_COMMENT + '-->',
                      '', data)

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return data

    @staticmethod
    @profile
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
    @profile
    def clean_text(text):
        # TODO: Improve this function if needed
        text = text.replace("&nbsp", " ")
        # text = re.sub(r'[^a-zA-Z0-9 ]',' ',text)
        text = re.sub('\s+', ' ', text).strip()
        # text = text.lower()
        return text

    @staticmethod
    @profile
    def extract_url(data):
        msg = 'Extracting url'
        logger.debug('%s %s', MSG_START, msg)

        # url = \
        #     re.findall("(?<=<!-- Mirrored from )(.*)(?= by HTTrack Website Copier)",
        #                str(data))[0]
        url = re.search("(?<=<!-- Mirrored from )(.*)(?= by HTTrack Website Copier)", str(data)).group()
        if url:
            if not url.startswith('http'):
                url = "http://" + url
            logger.debug("Url found: %s", url)
        else:
            url = None
            logger.debug("Url not found!")

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return url

    @staticmethod
    @profile
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
    @profile
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
    @profile
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
    @profile
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
    @profile
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
    def validate_doc_links_out1(doc, path_to_url):
        msg = "Validating document links_out"
        # logger.debug('%s %s', MSG_START, msg)

        dir = os.path.dirname(doc.path)
        links = []
        for link, text in doc.links_out:
            path = os.path.normpath(os.path.join(dir, link))
            if path not in path_to_url:
                path = os.path.normpath(os.path.join(path, 'index.html'))
            try:
                url = path_to_url[path]
                links.append((url, text))
            except Exception as e:
                pass
        doc.links_out = links

        # logger.debug('%s %s', MSG_SUCCESS, msg)
        return doc


    @staticmethod
    def validate_doc_links_out(doc, internal_url):
        msg = "Validating document links_out"
        # logger.debug('%s %s', MSG_START, msg)

        doc.links_out[:] = [(link, text) for (link, text) in doc.links_out if link in internal_url]
        # logger.debug('%s %s', MSG_SUCCESS, msg)
        return doc

    @staticmethod
    @profile
    def validate_docs_links_out(docs):
        msg = "Validating documents links_out"
        logger.info('%s %s', MSG_START, msg)

        # path_to_url = {}
        # for doc in docs:
        #     path_to_url[doc.path] = doc.url
        internal_urls = set([doc.url for doc in docs])

        docs = process_batch([(doc, internal_urls) for doc in docs], UCLParser.validate_doc_links_out)

        # logger.info('Validated unique urls: %d', len(urls))
        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @staticmethod
    def remove_duplicate_docs(docs):
        msg = "Removing duplicate documents"
        logger.info('%s %s', MSG_START, msg)
        url_to_path = {}
        paths_to_remove = set()
        for doc in docs:
            url = doc.url
            if url in url_to_path:
                found_doc = url_to_path[url]
                if len(found_doc.links_out) <= len(doc.links_out):
                    paths_to_remove.add(found_doc.path)
                else:
                    paths_to_remove.add(doc.path)
            else:
                url_to_path[url] = doc

        docs[:] = [doc for doc in docs if doc.path not in paths_to_remove]

        total_removed = len(paths_to_remove)
        logger.info('Removed %d document%s. Unique documents left: %d' % (total_removed, '' if total_removed == 1 else 's',len(docs)))
        logger.info('%s %s', MSG_SUCCESS, msg)

    @staticmethod
    @profile
    def add_links_in(docs):
        msg = 'Adding links_in'
        logger.info('%s %s', MSG_START, msg)

        docs_dict = {doc.url: doc for doc in docs}
        doc_links_in_keywords = {doc.url: set() for doc in docs}

        for url, doc in docs_dict.items():
            for link, text in doc.links_out:
                try:
                    docs_dict[link].links_in.append((url, text))
                    doc_links_in_keywords[url].add(text)
                except KeyError:
                    # this shouldn't happen
                    logger.error("Link not found: %s", link)
                    pass

        # print("Total docs: " + str(len(docs)))
        # docs = [doc for doc in docs if len(doc.links_in) > 0]
        # logger.info("Found docs with incoming links from other docs: %d", len(docs))

        for doc in docs:
            if doc.url in doc_links_in_keywords:
                doc.links_in_keywords = ', '.join([keyword.replace(',', ' ') for keyword in doc_links_in_keywords[doc.url]])

        logger.info('%s %s', MSG_SUCCESS, msg)
        return docs

    @staticmethod
    @profile
    def add_pagerank(docs, epochs=30, damping_factor=0.85):
        msg = 'Computing pageranks'
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
        print("Total docs: %d, Pagerank sum: %.3f" % (len(docs), s))
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
            "Keywords from Links In: {}\n" \
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



