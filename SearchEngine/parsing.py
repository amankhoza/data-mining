import os
import re

import logging
from urllib.request import pathname2url

from bs4 import BeautifulSoup
from bs4 import Comment

logger = logging.getLogger(__name__)

MSG_START = "[START]"
MSG_SUCCESS = "[SUCCESS]"
MSG_FAILED = "[FAILED]"


class UCLParser(object):
    NO_INDEX_COMMENT = 'noindex'
    NO_INDEX_END_COMMENT = 'endnoindex'

    def __init__(self, **kwargs):
        self.PARSER = kwargs.get('parser', 'html.parser')
        self.MIN_DATA_LEN = kwargs.get('min_data_len', 3000)

        self.local_path_to_url = None

    # def parse_file2(subdir, file):
    #     msg = "Parsing file "
    #     LOGGER.info(msg + MSG_START)
    #     LOGGER.info("%s %s", subdir, file)
    #     file_path_abs = os.path.join(subdir, file)
    #
    #     try:
    #         with open(file_path_abs, 'r', encoding='utf8') as f:
    #             data = f.read()
    #             soup = BeautifulSoup(data, PARSER)
    #
    #             LOGGER.info("Data length: %d", len(data))
    #
    #             if bool(soup) and len(data) > MIN_DATA_LEN:
    #
    #                 url = extract_url(soup)
    #                 if url:
    #                     doc = Document(path=file_path_abs)
    #                     doc.url = url
    #
    #                     doc.title = extract_title(soup)
    #                     doc.description = extract_description(soup)
    #                     doc.keywords = extract_keywords(soup)
    #                     doc.hrefs = extract_links(soup, subdir)
    #                     soup = get_clean_soup(data)
    #
    #                     doc.content = extract_content(soup)
    #
    #                     LOGGER.info(msg + MSG_SUCCESS)
    #                     return doc
    #                 else:
    #                     LOGGER.info(msg + MSG_FAILED)
    #
    #                     return None
    #
    #             else:
    #                 LOGGER.info("Invalid html!")
    #                 LOGGER.info(msg + MSG_FAILED)
    #                 return None
    #     except Exception as e:
    #         LOGGER.info(e)
    #         LOGGER.info(msg + MSG_FAILED)

    def parse_file(self, subdir, file_name):
        msg = "Parsing file "
        logger.debug('%s %s', MSG_START, msg)
        logger.info("Parsing %s%s", subdir, file_name)
        file_path_abs = os.path.join(subdir, file_name)

        doc = None

        try:
            with open(file_path_abs, 'r', encoding='utf8') as f:
                data = f.read()
                soup = BeautifulSoup(data, self.PARSER)

                if bool(soup) and len(data) > self.MIN_DATA_LEN:
                    try:
                        url = self.local_path_to_url[pathname2url(file_path_abs)]

                        logger.debug("Found url: %s", url)
                        doc = Document(path=file_path_abs, url=url)

                        doc.title = UCLParser.extract_title(soup)
                        doc.description = UCLParser.extract_description(soup)
                        doc.keywords = UCLParser.extract_keywords(soup)
                        doc.links = UCLParser.extract_links(soup, subdir, self.local_path_to_url)

                        data = UCLParser.remove_no_index(data)
                        soup = BeautifulSoup(data, self.PARSER)
                        soup = UCLParser.clean_soup(soup)
                        doc.content = UCLParser.extract_content(soup)
                    except KeyError:
                        logger.debug("Url not found in local_path_to_url!")
                else:
                    logger.debug("Invalid html!")
        except IOError as e:
            logger.warning("Problem opening file: %s", e)

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return doc

    def parse_files(self, root_dir):
        msg = "Parsing files from dir"
        logger.debug('%s %s', MSG_START, msg)
        logger.info("Parsing files from directory: %s", root_dir)

        self.local_path_to_url = UCLParser.index_local_path_to_url(root_dir)
        docs = []
        for subdir, dirs, files in os.walk(root_dir):
            for file in files:
                name, extension = os.path.splitext(file)
                if extension == '.html':
                    doc = self.parse_file(subdir, file)
                    if doc:
                        docs.append(doc)

        logger.info('Parsed %d documents', len(docs))
        logger.debug('%s %s', MSG_SUCCESS, msg)
        return docs

    # def remove_noindex_elements(self,soup):
    #     """
    #     Removes html elements after NO_INDEX comment.
    #
    #     :param soup:
    #     :return:
    #     """
    #
    #     msg = "Removing NO_INDEX elements "
    #     LOGGER.info(msg + MSG_START)
    #
    #     comments = soup(text=lambda text: isinstance(text, Comment))
    #     if comments:
    #         for comment in comments:
    #             if comment == self.NO_INDEX_COMMENT:
    #                 next_sibling = comment.findNextSibling()
    #                 if next_sibling:
    #                     # Remove element after NO_INDEX comment
    #                     next_sibling.extract()
    #
    #     LOGGER.info(msg + MSG_SUCCESS)
    #     return soup

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

        for element in soup.findAll(['br', 'script', 'style']):
            element.extract()

        # soup = self.remove_noindex_elements(soup)

        for comment in soup(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return soup

    # def extract_url(soup):
    #     msg = "Extracting url "
    #     LOGGER.info(msg + MSG_START)
    #
    #     try:
    #         for comment in soup(text=lambda text: isinstance(text, Comment)):
    #             pass
    #
    #         comment_txt = str(comment)
    #         parsed_url = comment_txt.split(' ')[3]
    #         if BASE_URL in parsed_url:
    #             url = parsed_url
    #             LOGGER.info("Valid url found: " + url)
    #             LOGGER.info(msg + MSG_SUCCESS)
    #             return url
    #     except Exception as e:
    #         LOGGER.info(e)
    #         LOGGER.info(msg + MSG_FAILED)
    #         return None

    @staticmethod
    def extract_links(soup, parent_dir, local_path_to_url):
        msg = 'Extracting links'
        logger.debug('%s %s', MSG_START, msg)

        links = []
        try:
            a_elements = soup.find('body').findAll('a', href=True)

            for a_elem in a_elements:
                href = a_elem['href']

                try:
                    path = os.path.normpath(os.path.join(parent_dir, href))
                    url = local_path_to_url[pathname2url(path)]
                    text = a_elem.text
                    links.append((url, text))
                except Exception:
                    # URL Not found in local_path_to_url
                    pass

        except Exception as e:
            logger.info("Could not extract links: %s", e)

        logger.debug('%s %s', MSG_SUCCESS, msg)
        return links

    @staticmethod
    def extract_title(soup):
        msg = 'Extracting title '
        logger.debug('%s %s', MSG_START, msg)

        title = ""
        try:
            title = soup.find('title').find(text=True)
            title = UCLParser.clean_text(title)
        except Exception as e:
            logger.info('Could not extract title: %s', e)

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
    def clean_text(text):
        # TODO: Improve this function if needed

        text = text.replace("&nbsp", " ")
        # text = re.sub(r'[^a-zA-Z0-9 ]',' ',text)
        text = re.sub('\s+', ' ', text).strip()
        # text = text.lower()
        return text

    @staticmethod
    def index_local_path_to_url(dir):
        """Creates an index where key is file local path and value is actual url"""
        msg = "Creating local to url index"
        logger.debug("%s %s", MSG_START, msg)
        logger.info("Creating local path to url index for: %s", dir)

        local_path_to_url = {}

        for subdir, dirs, files in os.walk(dir):
            for file in files:
                name, extension = os.path.splitext(file)
                file_path_abs = os.path.join(subdir, file)
                logger.debug('Parsing %s', file_path_abs)

                if extension == '.html':
                    try:
                        with open(file_path_abs, 'r', encoding='utf8') as f:
                            data = f.read()
                            try:
                                url = \
                                re.findall("(?<=<!-- Mirrored from )(.*)(?= by HTTrack Website Copier)", str(data))[0]
                                local_path_to_url[pathname2url(file_path_abs)] = url
                                logger.debug("Url found: %s", url)
                            except IndexError as e:
                                logger.debug("Url not found!")
                    except IOError as e:
                        logger.debug("Can't read file: %s", e)
                else:
                    logger.debug("File is not html!")

        logger.info("Total mappings: %d", len(list(local_path_to_url.keys())))

        # try:
        #     LOGGER.info("[DUMPING PICKLE]")
        #     with open(pickle_path, 'wb') as handle:
        #         pickle.dump(local_path_to_url, handle)
        #         LOGGER.info("[PICKLE DUMPED SUCCESSFULLY]")
        # except Exception as e:
        #     LOGGER.info("[PROBLEM CREATING PICKLE] %s", e)

        logger.debug("%s %s", MSG_SUCCESS, msg)
        return local_path_to_url


class Document(object):
    def __init__(self, **kwargs):
        self.path = kwargs.get('path', None)
        self.url = kwargs.get('url', None)
        self.title = kwargs.get('title', "")
        self.description = kwargs.get('description', "")
        self.keywords = kwargs.get('keywords', "")
        self.content = kwargs.get('content', "")
        self.links = kwargs.get('links', "")

    def __str__(self):
        return "Path: {}\nURL: {}\nTitle: {}\nDescription: {}\nKeywords: {}\nContent: {}\nLinks: {}\n".format(self.path,
                                                                                                              self.url,
                                                                                                              self.title,
                                                                                                              self.description,
                                                                                                              self.keywords,
                                                                                                              self.content,
                                                                                                              self.links)
