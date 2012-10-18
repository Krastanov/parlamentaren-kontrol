# -*- coding: utf-8 -*-
import datetime
import re
from HTMLParser import HTMLParser

import xlrd

from pk_db import db, cur
from pk_logging import logging
from pk_namedtuples import *
from pk_tools import urlopen, canonical_party_name


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
logger_excel = logging.getLogger('excel_parser')


class ExcelWarnings(object):
    def write(self, string):
        s = string.strip()
        if s:
            logger_excel.warning(s)
excel_warnings = ExcelWarnings()


registration_marker = u'РЕГИСТРАЦИЯ'
vote_marker = u'ГЛАСУВАНЕ'
parties_count = 6


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
    def MP_name_spellcheck(name):
        """Correct spelling errors in names of MPs"""
        tr_dict = {u'МАРИЯНА ПЕТРОВА ИВАНОВА-НИКОЛОВА': u'МАРИАНА ПЕТРОВА ИВАНОВА-НИКОЛОВА'}
        if name in tr_dict:
            logger_excel.warning("Spelling error: %s" % name)
            return tr_dict[name]
        return name

    def translate(reg_and_votes):
        """translate the registration and vote markers"""
        tr_reg = {u'О':'absent', u'П':'present', u'Р':'manually_registered'}
        reg = tr_reg[reg_and_votes[0]]
        votes = []
        tr_vote = {'+':'yes', '-':'no', '=':'abstain', '0':'absent'}
        for v in reg_and_votes[1:]:
            try:
                votes.append(tr_vote[v])
            except KeyError:
                logger_excel.warning("Strange expression found in by_name excell file. The expression is %s. We are dropping it."%repr(v))
        return [reg,] + votes

    book = xlrd.open_workbook(filename, logfile=excel_warnings)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows
    init_row = 2
    by_name_dict_transposed = {}
    for row in range(init_row, rows):
        raw = sheet.cell_value(rowx=row, colx=0).encode('UTF-8')
        array = [n.strip().upper() for n in raw.split()]
        name = MP_name_spellcheck(' '.join(array).decode('UTF-8'))
        party = canonical_party_name(sheet.cell_value(rowx=row, colx=3).strip().upper())
        key = rep_tuple(name=name, party=party)
        value = [sheet.cell_value(rowx=row, colx=col) for col in range(4, cols)]
        by_name_dict_transposed[key] = translate(value)
    reg_dict = {k:reg_and_votes[0] for k,reg_and_votes in by_name_dict_transposed.items()}
    keys, reg_and_votes = by_name_dict_transposed.keys(), by_name_dict_transposed.values()
    vote_list_of_dicts = [dict(zip(keys, v)) for v in zip(*reg_and_votes)[1:]]

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
    sessions = []
    row = 0
    while row < rows:
        first = sheet.cell_value(rowx=row, colx=0)
        if registration_marker in first:
            details_str = first.split(registration_marker)[-1].strip()
            row += 2
            per_party_dict = {}
            for i in range(parties_count):
                row += 1
                party = canonical_party_name(sheet.cell_value(rowx=row, colx=0).strip().upper())
                present = int(sheet.cell_value(rowx=row, colx=1))
                expected = int(sheet.cell_value(rowx=row, colx=2))
                per_party_dict[party] = reg_stats_per_party_tuple(present, expected)
            reg_by_party_dict = per_party_dict
        elif vote_marker in first:
            description = first.split(vote_marker)[-1].strip()
            row += 2
            votes_by_party_dict = {}
            for i in range(parties_count):
                row += 1
                party = canonical_party_name(sheet.cell_value(rowx=row, colx=0).strip().upper())
                yes = int(sheet.cell_value(rowx=row, colx=1))
                no = int(sheet.cell_value(rowx=row, colx=2))
                abstained = int(sheet.cell_value(rowx=row, colx=3))
                total = int(sheet.cell_value(rowx=row, colx=4))
                votes_by_party_dict[party] = vote_stats_per_party_tuple(yes, no, abstained, total)
            sessions.append(session_tuple(description, None, votes_by_party_dict))
        row += 1
    return reg_by_party_dict, sessions


##############################################################################
# Parse and save to disc.
##############################################################################
logger_to_db = logging.getLogger('to_db')


stenograms = {}
stenogram_IDs = open('data/IDs_plenary_stenograms').readlines()
for i, ID in enumerate(stenogram_IDs):
    problem_by_name = False
    problem_by_party = False
    ID = ID.strip()
    logger_to_db.info("Parsing stenogram %s - %d of %d." % (ID, i+1, len(stenogram_IDs)))

    f = urlopen('http://www.parliament.bg/bg/plenaryst/ID/'+ID)
    complete_stenogram_page = f.read().decode('utf-8')

    parser = StenogramsHTMLParser()
    parser.feed(complete_stenogram_page)
    date_string = parser.date.strftime('%d%m%y')


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
        problem_by_name = True


    try:
        filename = re.search(r"/pub/StenD/(\d*gv%s.xls)" % date_string, complete_stenogram_page).groups()[0]
        by_party_web = urlopen("http://www.parliament.bg/pub/StenD/%s" % filename)
        by_party_temp = open('data/temp.excel', 'wb')
        by_party_temp.write(by_party_web.read())
        by_party_temp.close()
        reg_by_party_dict, sessions = parse_excel_by_party('data/temp.excel')
    except Exception as e:
        logger_to_db.error("No party excel file was found for ID %s due to %s"%(ID,str(e)))
        reg_by_party_dict = {NA: reg_stats_per_party_tuple(1, 1)}
        sessions_dict = {NA: {NA: vote_stats_per_party_tuple(1, 1, 1, 1)}}
        problem_by_party = True


    sessions = [session_tuple(description,
                              votes_by_name,
                              votes_by_party_dict)
                for (description, nothing, votes_by_party_dict), votes_by_name
                    in zip(sessions, list_of_vote_dict_by_name)]

    stenograms[ID]=stgram_tuple(parser.date,
                                parser.data_list,
                                parser.votes_indices,
                                reg_by_name,
                                reg_by_party_dict,
                                sessions)

    if problem_by_name or problem_by_party:
        cur.execute("""INSERT INTO stenograms VALUES (%s, %s, %s, %s)""",
                    (parser.date, parser.data_list, parser.votes_indices, True))
    else:
        try:
            cur.execute("""INSERT INTO stenograms VALUES (%s, %s, %s, %s)""",
                        (parser.date, parser.data_list, parser.votes_indices, False))
            cur.executemany("""INSERT INTO party_reg VALUES (%s, %s, %s, %s)""",
                            ((k, parser.date, v.present, v.expected) for k,v in reg_by_party_dict.items()))
            cur.executemany("""INSERT INTO vote_sessions VALUES (%s, %s, %s)""",
                            ((parser.date, i, s.description) for i, s in enumerate(sessions)))
            cur.executemany("""INSERT INTO party_votes VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            ((party, parser.date, i, votes.yes, votes.no, votes.abstained, votes.total)
                                 for i, s in enumerate(sessions)
                                 for party, votes in s.votes_by_party_dict.items()))
            cur.executemany("""INSERT INTO mp_reg VALUES (%s, %s, %s, %s)""",
                            ((k.name, k.party, parser.date, v) for k,v in reg_by_name.items()))
            cur.executemany("""INSERT INTO mp_votes VALUES (%s, %s, %s, %s, %s)""",
                            ((mp.name, mp.party, parser.date, i, v)
                                 for i, s in enumerate(sessions)
                                 for mp, v in s.votes_by_name_dict.items()))
        except Exception as e:
            logger_to_db.error("Writting to db failed on stenogram %s due to %s" % (ID, str(e)))
    db.commit()
