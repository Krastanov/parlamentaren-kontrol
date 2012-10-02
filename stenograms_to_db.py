# -*- coding: utf-8 -*-
import cPickle
import datetime
import logging
import re
import urllib2
import warnings
from collections import namedtuple, OrderedDict
from HTMLParser import HTMLParser

import xlrd


##############################################################################
# Setup logging.
##############################################################################
logging.basicConfig(filename="log/log", filemode='a',
                    level=logging.INFO,
                    format='%(name)-16s: %(levelname)-8s %(message)s')
logging.captureWarnings(True)
console = logging.StreamHandler()
formatter = logging.Formatter('%(name)-16s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
warnings.formatwarning = lambda *args: re.sub("\n", "", args[0].message.strip())


##############################################################################
# Data Containers
##############################################################################
stgram_tuple = namedtuple('stgram_tuple', ['date', 'text_lines', 'in_text_votes',
                                           'reg_by_name_dict',
                                            # {rep_tuple: registered_bool}
                                           'reg_by_party_dict',
                                            # {name_string: reg_stats_per_party_tuple}
                                           'sessions',
                                            # [sesion_tuple]
                                           ])

rep_tuple = namedtuple('rep_tuple', ['name', 'party'])

session_tuple = namedtuple('session_tuple', ['description',
                                             'votes_by_name_dict',
                                                # {rep_tuple: vote_code_string}
                                             'votes_by_party_dict',
                                                # {name_string: vote_stats_per_party_tuple}
                                             ])

reg_stats_per_party_tuple = namedtuple('reg_stats_per_party_tuple', ['present', 'expected'])
vote_stats_per_party_tuple = namedtuple('vote_stats_per_party_tuple', ['yes', 'no', 'abstained', 'total'])

NA = u'Няма информация'


##############################################################################
# HTML Parsing
##############################################################################
logger_html = logging.getLogger('html_parser')

class StenogramsHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_marktitle = 0
        self.in_markcontent = False
        self.in_dateclass = False
        self.in_a = False
        self.in_ul = False
        self.data_list = []
        self.date = None
        self.votes_indices = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if self.in_marktitle:
                self.in_marktitle += 1
            if ('class', 'marktitle') in attrs:
                self.in_marktitle = 1
            elif ('class', 'markcontent') in attrs:
                self.in_markcontent = True
            elif ('class', 'dateclass') in attrs:
                self.in_dateclass = True

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_marktitle:
            self.in_marktitle -= 1
        elif tag == 'div' and self.in_markcontent:
            self.in_markcontent = False

    def handle_data(self, data):
        if self.in_dateclass:
            self.date = datetime.datetime.strptime(data.strip(), '%d/%m/%Y')
            self.in_dateclass = False
        elif self.in_markcontent:
            data = data.strip()
            how_many_have_voted_marker = u'Гласувал[и]?[ ]*\d*[ ]*народни[ ]*представители:'
            # The above marker regex must permit a number of spelling errors that can be present in the stenograms.
            if re.search(how_many_have_voted_marker, data):
                self.votes_indices.append(len(self.data_list))
            self.data_list.append(data)


##############################################################################
# Excel Parsing
##############################################################################
registration_marker = u'РЕГИСТРАЦИЯ'
vote_marker = u'ГЛАСУВАНЕ'
parties_count = 6

logger_excel = logging.getLogger('excel_parser')
class ExcelWarnings(object):
    def write(self, string):
        s = string.strip()
        if s:
            logger_excel.warning(s)
excel_warnings = ExcelWarnings()

def parse_excel_by_name(filename):
    """
    Parse excel files with vote statistics by representative.

    Assumptions
    ===========

    The .xls file starts with two lines we don't care about. All remaining lines
    contain the following fields, from left to right:
        - representative name
        - two fields we skip
        - representative's party
        - undefined number of fields containing stuff about how the
        representative voted.
    """
    book = xlrd.open_workbook(filename, logfile=excel_warnings)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows
    init_row = 2
    by_name_dict_transposed = {}
    for row in range(init_row, rows):
        name = sheet.cell_value(rowx=row, colx=0).strip().upper()
        party = sheet.cell_value(rowx=row, colx=3).strip().upper()
        key = rep_tuple(name=name, party=party)
        value = []
        for col in range(4, cols):
            value.append(sheet.cell_value(rowx=row, colx=col))
        by_name_dict_transposed[key] = value

    reg_dict = {k:votes[0] for k,votes in by_name_dict_transposed.items()}
    keys, votes = by_name_dict_transposed.keys(), by_name_dict_transposed.values()
    vote_list_of_dicts = [dict(zip(keys, v)) for v in zip(*votes)[1:]]

    return reg_dict, vote_list_of_dicts

def parse_excel_by_party(filename):
    u"""
    Parse excel files with vote statistics by party.

    One excel file per stenogram.

    Assumptions
    ===========

    - There is a total of six parties (see parties_count above)
    - For each session, there is a line containing either `vote_marker` or
    `registration_marker`, and that gives the kind of the session. There is
    only one registration per stenogram.
    - After this line, there are two lines we don't care about, and the next
    parties_count consecutive lines contain the vote/presence statistics by party.
    """
    book = xlrd.open_workbook(filename, logfile=excel_warnings)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows
    sessions_dict = OrderedDict()
    row = 0
    while row < rows:
        first = sheet.cell_value(rowx=row, colx=0)
        if registration_marker in first:
            details_str = first.split(registration_marker)[-1].strip()
            row += 2
            per_party_dict = {}
            for i in range(parties_count):
                row += 1
                party = sheet.cell_value(rowx=row, colx=0).strip().upper()
                present = int(sheet.cell_value(rowx=row, colx=1))
                expected = int(sheet.cell_value(rowx=row, colx=2))
                per_party_dict[party] = reg_stats_per_party_tuple(present, expected)
            reg_by_party_dict = per_party_dict
        elif vote_marker in first:
            details_str = first.split(vote_marker)[-1].strip()
            row += 2
            per_party_dict = {}
            for i in range(parties_count):
                row += 1
                party = sheet.cell_value(rowx=row, colx=0).strip().upper()
                yes = int(sheet.cell_value(rowx=row, colx=1))
                no = int(sheet.cell_value(rowx=row, colx=2))
                abstained = int(sheet.cell_value(rowx=row, colx=3))
                total = int(sheet.cell_value(rowx=row, colx=4))
                per_party_dict[party] = vote_stats_per_party_tuple(yes, no, abstained, total)
            sessions_dict[details_str] = per_party_dict
        row += 1
    return reg_by_party_dict, sessions_dict


##############################################################################
# Retry download
##############################################################################
def urlopen(url, retry=3):
    for i in range(retry):
        try:
            return urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            pass
    raise e


##############################################################################
# Parse and save to disc.
##############################################################################
if __name__ == '__main__':
    logger_to_db = logging.getLogger('to_db')
    stenograms = OrderedDict()
    stenogram_IDs = open('data/IDs_plenary_stenograms').readlines()
    for i, ID in enumerate(stenogram_IDs):
        ID = ID.strip()
        logger_to_db.info("Parsing stenogram %s - %d of %d." % (ID, i+1, len(stenogram_IDs)))

        logger_to_db.debug("Downloading html text.")
        f = urlopen('http://www.parliament.bg/bg/plenaryst/ID/'+ID)
        complete_stenogram_page = f.read().decode('utf-8')

        logger_to_db.debug("Parsing html text.")
        parser = StenogramsHTMLParser()
        parser.feed(complete_stenogram_page)

        date_string = parser.date.strftime('%d%m%y')

        logger_to_db.debug("Downloading and parsing votes-by-name excel data.")
        try:
            filename = re.search(r"/pub/StenD/(\d*iv%s.xls)" % date_string, complete_stenogram_page).groups()[0]
            by_name_web = urlopen("http://www.parliament.bg/pub/StenD/%s" % filename)
            by_name_temp = open('data/temp.excel', 'wb')
            by_name_temp.write(by_name_web.read())
            by_name_temp.close()
            reg_by_name, list_of_vote_dict_by_name = parse_excel_by_name('data/temp.excel')
        except Exception as e:
            logger_to_db.error("No name excel file was found for ID %s due to %s"%(ID,str(e)))
            reg_by_name = {rep_tuple(NA, NA): '0'}
            list_of_vote_dict_by_name = [reg_by_name]

        logger_to_db.debug("Downloading and parsing votes-by-party excel data.")
        try:
            filename = re.search(r"/pub/StenD/(\d*gv%s.xls)" % date_string, complete_stenogram_page).groups()[0]
            by_party_web = urlopen("http://www.parliament.bg/pub/StenD/%s" % filename)
            by_party_temp = open('data/temp.excel', 'wb')
            by_party_temp.write(by_party_web.read())
            by_party_temp.close()
            reg_by_party_dict, sessions_dict = parse_excel_by_party('data/temp.excel')
        except Exception as e:
            logger_to_db.error("No party excel file was found for ID %s due to %s"%(ID,str(e)))
            reg_by_party_dict = {NA: reg_stats_per_party_tuple(1, 1)}
            sessions_dict = {NA: {NA: vote_stats_per_party_tuple(1, 1, 1, 1)}}

        logger_to_db.debug("Building list of sessions for the stenogram.")
        sessions = [session_tuple(description,
                                  votes_by_name,
                                  votes_by_party)
                    for (description, votes_by_party), votes_by_name
                        in zip(sessions_dict.items(), list_of_vote_dict_by_name)]

        logger_to_db.debug("Adding the complete stenogram object to the dictionary of stenograms.")
        stenograms[ID]=stgram_tuple(parser.date,
                                    parser.data_list,
                                    parser.votes_indices,
                                    reg_by_name,
                                    reg_by_party_dict,
                                    sessions)

    logger_to_db.info("Dumping the database to disk.")
    stenograms_dump = open('data/stenograms_dump', 'w')
    cPickle.dump(stenograms, stenograms_dump, 2)
    stenograms_dump.close()
