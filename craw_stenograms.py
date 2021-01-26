import datetime
import re

import xlrd

from pk_db import db, cur
from pk_logging import logging, logger_workaround
from pk_namedtuples import *
from pk_tools import urlopen, canonical_party_name, StenogramsHTMLParser
canonical_party_name = lambda a:a

##############################################################################
# Excel Parsing
##############################################################################
logger_excel = logging.getLogger('excel_parser')
logger_excel_lib = logging.getLogger('excel_parser_lib')


class ExcelWarnings(object):
    def write(self, string):
        s = string.strip()
        if s:
            logger_excel_lib.warning(s)
excel_warnings = ExcelWarnings()


registration_marker = u'РЕГИСТРАЦИЯ'
vote_marker = u'ГЛАСУВАНЕ'

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
    # XXX Workarounds
    # Correct spelling errors in names of MPs.
    def MP_name_spellcheck(name):
        tr_dict = {u'МАРИЯНА ПЕТРОВА ИВАНОВА-НИКОЛОВА': u'МАРИАНА ПЕТРОВА ИВАНОВА-НИКОЛОВА',
                   u'ВЕНЦЕСЛАВ ВАСИЛЕВ ВЪРБАНОВ': u'ВЕНЦИСЛАВ ВАСИЛЕВ ВЪРБАНОВ',
                   u'АЛЕКСАНДЪР СТОЙЧЕВ СТОЙЧЕВ': u'АЛЕКСАНДЪР СТОЙЧЕВ СТОЙКОВ'}
        if name in tr_dict:
            logger_workaround.warning("Spelling error: %s" % name)
            return tr_dict[name]
        return name
    # Remove unregistered MPs.
    def filter_names(*args):
        to_filter_out = [u'МИХАИЛ ВЛАДИМИРОВ ВЛАДОВ', u'НИКОЛАЙ НАНКОВ НАНКОВ']
        zip_args = zip(*args)
        filtered = filter(lambda a: a[0] not in to_filter_out, zip_args)
        if len(filtered) != len(zip_args):
            logger_workaround.warning("An MP was filtered out of the by-names list, because they are not registered as an MP.")
            return zip(*filtered)
        return args
    # XXX End of Workarounds.

    # Translate the registration and vote markers.
    tr_reg = {u'О':'absent', u'П':'present', u'Р':'manually_registered'}
    tr_vote = {'+':'yes', '-':'no', '=':'abstain', '0':'absent'}

    book = xlrd.open_workbook(filename, logfile=excel_warnings)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows

    names = [MP_name_spellcheck(' '.join(sheet.cell_value(rowx=row, colx=0).upper().split()))
             for row in range(2, rows)]
    parties = [canonical_party_name(sheet.cell_value(rowx=row, colx=3).strip().upper())
               for row in range(2, rows)]
    reg_sessions = []
    vote_sessions = []
    for col in range(4, cols):
        values = [sheet.cell_value(rowx=row, colx=col) for row in range(2, rows)]
        if all(v in tr_reg.keys() for v in values):
            reg_sessions.append([tr_reg[v] for v in values])
        elif all(v in tr_vote.keys() for v in values):
            vote_sessions.append([tr_vote[v] for v in values])
        elif all(v=='' for v in values):
            logger_excel.warning("Empty column found in the by_names excell file. Skipping it.")
        else:
            logger_excel.error("Strange column found in the by_names excell file. Skipping it.")
    vote_sessions = zip(*vote_sessions)

    if len(reg_sessions) > 1:
        logger_excel.warning("There are more than one registration for this stenogram.")
    elif len(reg_sessions) != 1:
        raise ValueError('No registrations detected in the by-names file.')

    return filter_names(names, parties, reg_sessions[-1], vote_sessions)


def parse_excel_by_party(filename):
    u"""
    Parse excel files with vote statistics by party.

    One excel file per stenogram.

    Assumptions
    ===========

    - The number of parties per vote is always the same.
    - For each session, there is a line containing either `vote_marker` or
    `registration_marker`, and that gives the kind of the session. There is
    only one registration per stenogram.
    - After this line, there are two lines we don't care about, and the next
    parties_count consecutive lines contain the vote/presence statistics by party.
    """
    book = xlrd.open_workbook(filename, logfile=excel_warnings)
    sheet = book.sheet_by_index(0)
    rows = sheet.nrows
    sessions = []
    assert registration_marker in sheet.cell_value(rowx=1,colx=0), "No registration marker"
    assert 'ПГ' in sheet.cell_value(rowx=2,colx=0), "No ПГ marker"
    assert 'Общо' in sheet.cell_value(rowx=3,colx=0), "No Общо marker"
    row = 4
    parties_count = 0
    while row < rows:
        cell = sheet.cell_value(rowx=row,colx=0)
        if vote_marker in cell:
            break
        if 'НЕЗ' in cell:
            parties_count += 1
            break
        row += 1
        parties_count += 1
    else:
        logger_to_db.error('Could not reliably find parties_count in %s'%filename)
        raise ValueError('Could not reliably find parties_count')
    row = 0
    while row < rows:
        first = sheet.cell_value(rowx=row, colx=0)
        if registration_marker in first:
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
            time, description = description.split(u'по тема')
            time = datetime.datetime.strptime(time[-6:], '%H:%M ')
            description = description.strip()
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
            sessions.append(session_tuple(description, time, None, votes_by_party_dict))
        row += 1
    return reg_by_party_dict, sessions


##############################################################################
# Parse and save to disc.
##############################################################################
logger_to_db = logging.getLogger('stenograms_to_db')


cur.execute("""SELECT original_url FROM stenograms""")
urls_already_in_db = set(_[0] for _ in cur.fetchall())
stenogram_IDs = []
assemblies_and_ids = [(7,41),(50,42),(51,43),(52,44)] # XXX Hardcoded values
all_parties = set()
for internal_id, assembly_number in assemblies_and_ids:
    stenogram_IDs += [(i, 'https://www.parliament.bg/bg/plenaryst/ns/%d/ID/'%internal_id+i)
                      for i in map(str.strip, open('craw_data/IDs_plenary_stenograms_%d'%assembly_number).readlines())]


for i, (ID, original_url) in enumerate(stenogram_IDs):
    if original_url in urls_already_in_db:
        continue

    problem_by_name = False
    problem_by_party = False
    logger_to_db.info("Parsing stenogram %s - %d of %d." % (ID, i+1, len(stenogram_IDs)))

    try:
        filename = './craw_data/stenograms/%s.html'%ID
        f = open(filename)
        complete_stenogram_page = f.read()
        parser = StenogramsHTMLParser(complete_stenogram_page)
        date_string = parser.date.strftime('%d%m%y')
    except Exception as e:
        logger_to_db.error("Parsing problem with ID %s. %s"%(ID,str(e)))
        continue

    try:
        filename = './craw_data/stenograms/%s-%s-g.xls'%(ID,date_string)
        reg_by_party_dict, sessions = parse_excel_by_party(filename)
    except Exception as e:
        logger_to_db.error("No party excel file was found for ID %s due to %s"%(ID,str(e)))
        problem_by_party = True

    from pprint import pprint
    #pprint(reg_by_party_dict)
    size = len(all_parties)
    all_parties.update(set(reg_by_party_dict.keys()))
    print('\r',i+1,'      ',end='',flush=True)
    if size!=len(all_parties):
        print()
        pprint(all_parties)
        print()
    continue

    try:
        filename = './craw_data/stenograms/%s-%s-i.xls'%(ID,date_string)
        if ID == '2766': # XXX Workaround malformated excel file.
            logger_workaround.warning('Using the workaround for ID 2766.')
            mp_names, mp_parties, mp_reg_session, mp_vote_sessions = parse_excel_by_name('workarounds/iv050712_ID2766_line32-33_workaround.xls')
        else:
            mp_names, mp_parties, mp_reg_session, mp_vote_sessions = parse_excel_by_name(filename)
    except Exception as e:
        logger_to_db.error("No MP name excel file was found for ID %s due to %s"%(ID,str(e)))
        problem_by_name = True


    if problem_by_name or problem_by_party:
        cur.execute("""INSERT INTO stenograms VALUES (%s, %s, %s, %s, %s)""",
                    (parser.date, parser.data_list, parser.votes_indices, True, original_url))
    else:
        try:
            assert all([len(sessions) == len(mp_votes) for mp_votes in mp_vote_sessions]), "Not all sessions are recorded."
            cur.execute("""INSERT INTO stenograms VALUES (%s, %s, %s, %s, %s)""",
                        (parser.date, parser.data_list, parser.votes_indices, False, original_url))
            cur.executemany("""INSERT INTO party_reg VALUES (%s, %s, %s, %s)""",
                            ((k, parser.date, v.present, v.expected) for k,v in reg_by_party_dict.items()))
            cur.executemany("""INSERT INTO vote_sessions VALUES (%s, %s, %s, %s)""",
                            ((parser.date, i, s.description, s.time) for i, s in enumerate(sessions)))
            cur.executemany("""INSERT INTO party_votes VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            ((party, parser.date, i, votes.yes, votes.no, votes.abstained, votes.total)
                                 for i, s in enumerate(sessions)
                                 for party, votes in s.votes_by_party_dict.items()))
            cur.executemany("""INSERT INTO mp_reg VALUES (%s, %s, %s, %s)""",
                            ((name, party, parser.date, reg) for name, party, reg in zip(mp_names, mp_parties, mp_reg_session)))
            cur.executemany("""INSERT INTO mp_votes VALUES (%s, %s, %s, %s, %s)""",
                            ((name, party, parser.date, i, v)
                                 for name, party, votes in zip(mp_names, mp_parties, mp_vote_sessions)
                                 for i, v in enumerate(votes)))
        except Exception as e:
            logger_to_db.error("Writting to db failed on stenogram %s due to %s" % (ID, str(e)))
    db.commit()
