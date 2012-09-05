from HTMLParser import HTMLParser
from urllib2 import urlopen
from collections import namedtuple, OrderedDict
import xlrd
import shelve


##############################################################################
# Data Containers
##############################################################################
stgram_tuple = namedtuple('stgram_tuple', ['date', 'text_lines',
                                           'reg_by_name_dict',
                                            # {name_string: registered_bool}
                                           'reg_by_party_dict',
                                            # {name_string: reg_stats_per_party_tuple}
                                           'sessions',
                                            # [sesion_tuple]
                                           ])

rep_tuple = namedtuple('rep_tuple', ['name', 'party'])

session_tuple = namedtuple('session_tuple', ['description',
                                             'votes_by_name_dict',
                                                # {name_string: vote_code_string}
                                             'votes_by_party_dict',
                                                # {name_string: vote_stats_per_party_tuple}
                                             ])

reg_stats_per_party_tuple = namedtuple('reg_stats_per_party_tuple', ['present', 'expected'])
vote_stats_per_party_tuple = namedtuple('vote_stats_per_party_tuple', ['yes', 'no', 'abstained', 'total'])


##############################################################################
# HTML Parsing
##############################################################################
class StenogramsHTMLParser(HTMLParser):
    # TODO text_lines does not contain all the content

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_marktitle = 0
        self.in_dateclass = False
        self.data_list = []
        self.date = None

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if self.in_marktitle:
                self.in_marktitle += 1

            if ('class', 'marktitle') in attrs:
                self.in_marktitle = 1
            elif ('class', 'dateclass') in attrs:
                self.in_dateclass = True

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_marktitle:
            self.in_marktitle -= 1

    def handle_data(self, data):
        if self.in_dateclass:
            self.date = data.strip() #TODO there must be a date type
            self.in_dateclass = False
        elif self.in_marktitle:
            self.data_list.append(data)


##############################################################################
# Excel Parsing
##############################################################################
registration_marker = u'\u0420\u0415\u0413\u0418\u0421\u0422\u0420\u0410\u0426\u0418\u042f'
vote_marker = u'\u0413\u041b\u0410\u0421\u0423\u0412\u0410\u041d\u0415'
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
    book = xlrd.open_workbook(filename)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows
    init_row = 2
    result = {}
    for row in range(init_row, rows):
        name = sheet.cell_value(rowx=row, colx=0).strip().upper()
        party = sheet.cell_value(rowx=row, colx=3).strip().upper()
        key = rep_tuple(name=name, party=party)
        value = []
        for col in range(4, cols):
            value.append(sheet.cell_value(rowx=row, colx=col))
        result[key] = tuple(value)

    return result

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
    book = xlrd.open_workbook(filename)
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
# Parse and save to disc.
##############################################################################
if __name__ == '__main__':
    stenograms = {}
    stenogram_IDs = open('data/IDs_plenary_stenograms').readlines()
    for ID in stenogram_IDs[:2]:
        ID = ID.strip()
        print "###########"
        print "#### At ID: ", ID
        print "###########"
        print "- downloading and parsing HTML data"
        parser = StenogramsHTMLParser()
        f = urlopen('http://www.parliament.bg/bg/plenaryst/ID/'+ID)
        parser.feed(f.read().decode('utf-8'))

        day, month, year = parser.date.split('/')# TODO the next 3 lines should use the datetype
        date_string = day + month + year[2:]

        print "- downloading and parsing votes-by-name excel data"
        by_name_temp = open('data/temp_name.excel', 'wb')
        by_name_web = urlopen("http://www.parliament.bg/pub/StenD/iv%s.xls" % date_string)
        by_name_temp.write(by_name_web.read())
        by_name_temp.close()
        by_name_dict = parse_excel_by_name('data/temp_name.excel')

        print "- downloading and parsing votes-by-party excel data"
        by_party_temp = open('data/temp_party.excel', 'wb')
        by_party_web = urlopen("http://www.parliament.bg/pub/StenD/gv%s.xls" % date_string)
        by_party_temp.write(by_party_web.read())
        by_party_temp.close()
        reg_by_party_dict, sessions_dict = parse_excel_by_party('data/temp_party.excel')

        sessions = [session_tuple(description,
                                  None,
                                  votes_by_party)
                    for (description, votes_by_party) in sessions_dict.items()]

        stenograms[ID]=stgram_tuple(parser.date,
                                    parser.data_list,
                                    None,
                                    reg_by_party_dict,
                                    sessions)

    stenograms_dump = shelve.open('data/stenograms_dump')
    stenograms_dump['stenograms'] = stenograms
    stenograms_dump.close()
