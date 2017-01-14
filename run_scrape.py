#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
import logging
import os
import time
from bs4 import BeautifulSoup
import sys
import csv
import re
import argparse
import requests

logger = logging.getLogger('scrape')

parser = argparse.ArgumentParser(description="Scrape site of urls")
parser.add_argument("--site-url", help="", required=True)
parser.add_argument("--browser", help="", required=True)
parser.add_argument("--follow", help="", default=0, type=int)
parser.add_argument("--exclude-links-keys", nargs='+',
                    help="exclude links which text contains all keys")
parser.add_argument("--exclude-links-any-key", nargs='+',
                    help="exclude links which text contains any key")
parser.add_argument("--retain-links-keys", nargs='+',
                    help="retain links which text match all keys")
parser.add_argument("--retain-links-any-key", nargs='+',
                    help="retain links which text match any key")
parser.add_argument("--retain-regex", help="retain links which text match regex")
parser.add_argument("--exclude-regex", help="exclude links which text match regex")
parser.add_argument("--verbose", help="be more verbose", default=False, action="store_true")
parser.add_argument("--unite", help="unite and apply regex conditions in the following order:"
                                    "--retain-links-any-key, --retain-links-keys, --exclude-links-any-key,"
                                    "--exclude-links-keys", default=False, action="store_true")
args = parser.parse_args()
arg_dict = vars(args)


class Scrape:

    def __init__(self, site_url_, browser_):

        self.site_url = site_url_
        self.root_domain = site_url_
        self.matched_ = []
        csv_file = "{}.csv".format(time.strftime('%d%m%y%H%M', time.localtime()))
        self.csv_file = os.path.join(os.path.dirname(__file__), 'csv', csv_file)
        self.driver = None
        self.display = None

        if browser_ == 'Chrome-OSX':
            self.driver = webdriver.Chrome()
            self.driver.get(self.site_url)
        elif browser_ == 'Chrome-Headless':
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()
            self.driver = webdriver.Chrome()
            self.driver.get(self.site_url)

    def scrape(self):

        try:
            logger.info('Scraping: {}'.format(self.site_url))
            if self.driver:
                links = self._grab_all_links()
            else:
                links = self._soup_all_links()

            for text_href in self._extract(links, arg_dict['unite']):
                self.matched_.append(text_href)
            logger.info('Scraped: {}'.format(self.site_url))
        except:
            logger.error('_grab_all_links error', exc_info=True)

    def crawl(self):

        temp = self.matched_
        self.matched_ = []

        for page in temp:
            url = page[1]
            if self.driver:
                try:
                    self.driver.get(url)
                except TimeoutException:
                    logger.warning('crawl driver get timed out on page: {}'.format(url))
                    continue
                except:
                    logger.error('crawl error', exc_info=True)
                    continue
            self.site_url = url
            self.scrape()

    def _open_page(self, url):

        """
        :param url: url to open
        """

        if self.driver:
            self.driver.get(url)
        else:
            requests.get(url)

    def _process_href(self, href):

        """
        :param href: href to process
        :return: processed href; javascript, None hrefs are dropped
        """

        if not href:
            return None
        elif href.startswith('http'):
            return href
        elif href.startswith('javascript'):
            return None
        else:
            return '{}{}'.format(self.root_domain, href)

    def _extract(self, links, unite):

        """
        :param links: links to search for regex match
        :return: all links matching regex
        * if more than one argument get passed in to the script e.g.
        --retain-links-any-key, --retain-links-key AND --unite is false,
        all links are processed by --retain-links-any-key, appended to a list
        and then again all links are processed by --retain-links-key and appended,
        so the the end result match any of these arguments
        * in the case of the --unite setting set to true, links are processed
        sequentially e.g. all links are processed by --retain-links-any-key and then
        the returned list of matching links is processed by --retain-links-key, so the
        end result match all arguments passed in.
        * --retain-regex and --exclude-regex deactivate the other arguments, so links either
        match or dont match the regex passed in
        """

        extracted_ = []

        def log_match(log_data):
            for record in log_data:
                logger.info(record)
                self._write_row(record)
                if record not in extracted_:
                    extracted_.append(record)
                else:
                    logger.debug('Record already on list: {}'.format(record))

        # arg: --retain-regex
        if arg_dict['retain_regex']:
            rs_ = []
            logger.info('== args ==: --retain-regex regex: {}'.format(arg_dict['retain_regex']))
            self._write_row(['### args: --retain-regex {}'.format(arg_dict['retain_regex']),
                             'Source page: {}'.format(self.site_url)])
            for link_text in links:
                regex_ = r"{}".format(arg_dict['retain_regex'])
                comp_ = re.compile(regex_)
                match_ = comp_.search(link_text[0])
                if match_:
                    logger.debug('retain_regex regex \'{}\' match found in \'{}\''.
                                 format(regex_, link_text[0].encode('utf-8')))
                    rs_.append(link_text)

            log_match(rs_)
            return extracted_

        # arg: --exclude-regex
        if arg_dict['exclude_regex']:
                rs_ = []
                logger.info('== args ==: --exclude-regex: {}'.format(arg_dict['exclude_regex']))
                self._write_row(['### args: --exclude-regex {}'.format(arg_dict['exclude_regex']),
                                 'Source page: {}'.format(self.site_url)])
                for link_text in links:
                    regex_ = r"{}".format(arg_dict['exclude_regex'])
                    comp_ = re.compile(regex_)
                    match_ = comp_.search(link_text[0])
                    if not match_:
                        logger.debug('exclude_regex regex \'{}\' match not found in \'{}\''.
                                     format(regex_, link_text[0].encode('utf-8')))
                        rs_.append(link_text)

                log_match(rs_)
                return extracted_

        # arg: --retain-links-any-key (match any key)
        if arg_dict['retain_links_any_key']:
            rs_ = self._retain_any_key(links)
            logger.info('== args ==: --retain-links-any-key {}'.format(arg_dict['retain_links_any_key']))
            self._write_row(['### args: --retain-links-any-key {}, --unite {}'.
                            format(arg_dict['retain_links_any_key'], unite),'Source page: {}'.format(self.site_url)])
            if not unite:
                log_match(rs_)
            else:
                links = rs_

        # arg: --retain-links-key (match all keys)
        if arg_dict['retain_links_keys']:
            rs_ = self._retain_keys(links)
            logger.info('== args ==: --retain-links-key {}'.format(arg_dict['retain_links_keys']))
            self._write_row(['### args: --retain-links-key {}, --unite {}'.
                            format(arg_dict['retain_links_keys'], unite),'Source page: {}'.format(self.site_url)])
            if not unite:
                log_match(rs_)
            else:
                links = rs_

        # arg: --exclude-links-any-key
        if arg_dict['exclude_links_any_key']:
            rs_ = self._exclude_any_key(links)
            logger.info('== args ==: --exclude-links-any-key {}'.format(arg_dict['exclude_links_any_key']))
            self._write_row(['### args: --exclude-links-any-key {}, --unite {}'.
                            format(arg_dict['exclude_links_any_key'], unite),'Source page: {}'.format(self.site_url)])
            if not unite:
                log_match(rs_)
            else:
                links = rs_

        # arg: --exclude-links-keys
        if arg_dict['exclude_links_keys']:
            rs_ = self._exclude_keys(links)
            logger.info('== args ==: --exclude-links-keys {}'.format(arg_dict['exclude_links_keys']))
            self._write_row(['### args: --exclude-links-keys {}, --unite {}'.
                            format(arg_dict['exclude_links_keys'], unite),'Source page: {}'.format(self.site_url)])
            if not unite:
                log_match(rs_)

        if unite:
            log_match(rs_)

        return extracted_

    def _retain_any_key(self, links):

        """
        :param links: to search through regular expression
        :return: list[text, href] matching any key
        """

        result_set = []
        for key_ in arg_dict['retain_links_any_key']:
            for link_text in links:
                if self._apply_lookahead(link_text[0], key_):
                    result_set.append(link_text)
        return result_set

    def _retain_keys(self, links):

        """
        :param links: to search through regular expression
        :return: list[text, href] matching all keys
        """

        for key_ in arg_dict['retain_links_keys']:
            _temp = []
            for link_text in links:
                if self._apply_lookahead(link_text[0], key_):
                    _temp.append(link_text)
            links = _temp
        return _temp

    def _exclude_any_key(self, links):

        """
        :param links: to search through regular expression
        :return: list[text, href]
        """

        for key_ in arg_dict['exclude_links_any_key']:
            _temp = []
            for link_text in links:
                if self._apply_negative_lookahead(link_text[0], key_):
                    _temp.append(link_text)
            links = _temp
        return _temp

    def _exclude_keys(self, links):

        """
        :param links: to search through regular expression
        :return: list[text, href]
        """

        result_set = []
        for link_text in links:
            _temp = []
            for key_ in arg_dict['exclude_links_keys']:
                if self._apply_negative_lookahead(link_text[0], key_):
                    _temp.append(True)
            if any(_temp):
                result_set.append(link_text)
        return result_set

    def _grab_all_links(self):

        """ grab all html a tags
            append them to a list [text, href]
            using: webdriver/selenium
        """

        try:
            links_ = []
            els = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))
            for el in els:
                heading = el.text.strip()
                href_ = el.get_attribute('href')
                href_ = self._process_href(href_)
                if href_:
                    links_.append([heading, href_])
                    logger.debug('Link grabbed: text: {}, href: {}'.format(heading.encode('utf-8'), href_))

        except StaleElementReferenceException:
            logger.warning('_grab_all_links element stale ... ')
        except TimeoutException:
            logger.info('_grab_all_links timed out. no links on page.')
        except:
            logger.error('_grab_all_links error', exc_info=True)
        finally:
            return links_

    def _soup_all_links(self):

        """ grab all links - html tag name a
            save them as a list [text, href]
            using: soup
        """

        links_ = []
        req = requests.get(self.site_url)
        soup = BeautifulSoup(req.text, 'lxml')
        for a_ in soup.find_all('a'):
            href_ = self._process_href(a_.get('href'))
            if href_:
                links_.append([a_.text, href_])
                logger.debug('Link grabbed: text: {}, href: {}'.format(a_.text.encode('utf-8'), href_))
        return links_

    def _write_row(self, row):
        with open(self.csv_file, 'ab') as hlr:
            wrt = csv.writer(hlr, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if isinstance(row, list):
                row_str = '$split'.join(row)
                row = row_str.encode('utf-8').split('$split')
            wrt.writerow(row)
            logger.info('Add row: {} to file: {}'.format(row, self.csv_file))

    def tear_down(self):
        if self.driver:
            self.driver.quit()
        if self.display:
            self.display.stop()

    @staticmethod
    def _apply_lookahead(source_, ahead_word):
        # case insensitive
        regex_ = r"(?i)(?={})".format(ahead_word)
        comp_ = re.compile(regex_)
        match_ = comp_.search(source_)
        if match_:
            logger.debug('_apply_lookahead match found: \'{}\' in \'{}\''.
                         format(ahead_word, source_.encode('utf-8')))
            return True

    @staticmethod
    def _apply_negative_lookahead(source_, ahead_word):
        # case insensitive
        regex_ = r"(?i)^((?!{}).)*$".format(ahead_word)
        comp_ = re.compile(regex_)
        match_ = comp_.search(source_)
        if match_:
            logger.debug('_apply_negative_lookahead match found: \'{}\' in \'{}\''.
                         format(ahead_word, source_.encode('utf-8')))
            return True


if __name__ == '__main__':

    # timestamp = time.strftime('%d%m%y', time.localtime())  # comment in for production
    # log = 'logs'
    timestamp = ''
    log = ''
    log_file = os.path.join(os.path.dirname(__file__), log,
                            timestamp + "_scraper.log")
    file_hndlr = logging.FileHandler(log_file)
    logger.addHandler(file_hndlr)
    console = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(console)
    ch = logging.Formatter('[%(levelname)s] %(message)s')
    console.setFormatter(ch)
    file_hndlr.setFormatter(ch)
    logger.setLevel('DEBUG')

    browser = arg_dict['browser']
    site_url = "http://{}".format(arg_dict['site_url'])

    # --verbose for console handler
    # file handler is by default verbose
    if arg_dict['verbose']:
        console.setLevel(logging.getLevelName('DEBUG'))
    else:
        console.setLevel(logging.getLevelName('INFO'))
    logger.info('CLI args: {}'.format(arg_dict))

    scrape = Scrape(site_url, browser)
    scrape.scrape()

    # --follow: fow far to follow links
    # e.g follow = 2, grab links from the page
    # and open them (1), grab links from all pages
    # that were opened (1) and open them up (2)
    for counter in range(arg_dict['follow']):
        scrape.crawl()

    scrape.tear_down()