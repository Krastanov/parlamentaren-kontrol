from HTMLParser import HTMLParser
from urllib2 import urlopen
from collections import namedtuple, OrderedDict
import xlrd
import shelve


################
###
### HTML PARSING
###
################

class StenogramsHTMLParser(HTMLParser):

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


stgram = namedtuple('stgram', ['date', 'text_lines', 'by_name_votes', 'by_party_votes'])


#################
###
### EXCEL PARSING
###
#################

# TODO rename these so it is obvious that they are containers
# for instance a suffix _tuple
rep = namedtuple('rep', ['name', 'party'])
session = namedtuple('session', ['kind', 'details'])
reg_stats = namedtuple('reg_stats', ['present', 'expected'])
vote_stats = namedtuple('vote_stats', ['yes', 'no', 'abstained', 'total'])

registration = u'\u0420\u0415\u0413\u0418\u0421\u0422\u0420\u0410\u0426\u0418\u042f'
vote = u'\u0413\u041b\u0410\u0421\u0423\u0412\u0410\u041d\u0415'

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

    Returns
    =======

    The result is a
        dictionary:
            key: a namedtuple containing the name and party of the representative
            value: a tuple containing the vote statistics for this representative

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
        key = rep(name=name, party=party)
        value = []
        for col in range(4, cols):
            value.append(sheet.cell_value(rowx=row, colx=col))
        result[key] = tuple(value)

    return result

def parse_excel_by_party(filename):
    u"""
    Parse excel files with vote statistics by party.

    Assumptions
    ===========

    - There is a total of six parties (see parties_count above)
    - For each session, there is a line containing either "GLASUVANE" or
    "REGISTRACIA", and that's how we know what's going on
    - After this line, there are two lines we don't care about, and the next
    parties_count consecutive lines contain the vote/presence statistics by party.

    Returns
    =======

    The result is a
        dictionary:
            key: namedtuple describing the session type and additional details
            value:
                dictionary:
                    key: party
                    value:
                        namedtuple:
                            key: present/expected for 'REGISTRACIA', or
                                 for/against/skipped/total for 'GLASUVANE'
                            value: corresponding numbers in int format

    """
    book = xlrd.open_workbook(filename)
    sheet = book.sheet_by_index(0)
    cols = sheet.ncols
    rows = sheet.nrows
    result = OrderedDict()
    row = 0
    while row < rows:
        first = sheet.cell_value(rowx=row, colx=0)
        if registration in first:
            kind = registration
            details = first.split(registration)[-1].strip()
            key = session(kind=kind, details=details)
            row += 2
            value = {}
            for i in range(parties_count):
                row += 1
                party = sheet.cell_value(rowx=row, colx=0).strip().upper()
                present = int(sheet.cell_value(rowx=row, colx=1))
                expected = int(sheet.cell_value(rowx=row, colx=2))
                value[party] = reg_stats(present=present, expected=expected)
            result[key] = value
        elif vote in first:
            kind = vote
            details = first.split(vote)[-1].strip()
            key = session(kind=kind, details=details)
            row += 2
            value = {}
            for i in range(parties_count):
                row += 1
                party = sheet.cell_value(rowx=row, colx=0).strip().upper()
                yes = int(sheet.cell_value(rowx=row, colx=1))
                no = int(sheet.cell_value(rowx=row, colx=2))
                abstained = int(sheet.cell_value(rowx=row, colx=3))
                total = int(sheet.cell_value(rowx=row, colx=4))
                value[party] = vote_stats(yes=yes, no=no, abstained=abstained, total=total)
            result[key] = value
        row += 1
    return result

def pprint_result_by_party(result):
    """
    Print the output of the parser for results by party.

    So that it makes more sense.

    """
    for key, value in result.items():
        print key.kind
        print key.details
        for value_key, value_value  in value.items():
            print value_key, ':', value_value




if __name__ == '__main__':
    stenograms = {}
    stenogram_IDs = open('data/IDs_plenary_stenograms').readlines()
    for ID in stenogram_IDs[:2]:
        ID = ID.strip()
        print "At ID: ", ID
        parser = StenogramsHTMLParser()
        f = urlopen('http://www.parliament.bg/bg/plenaryst/ID/'+ID)
        parser.feed(f.read().decode('utf-8'))
        print parser.date

        day, month, year = parser.date.split('/')# TODO the next 3 lines should use the datetype
        date_string = day + month + year[2:]

        by_name_temp = open('data/temp_name.excel', 'wb')
        by_name_web = urlopen("http://www.parliament.bg/pub/StenD/iv%s.xls" % date_string)
        by_name_temp.write(by_name_web.read())
        by_name_temp.close()
        by_name_dict = parse_excel_by_name('data/temp_name.excel')

        by_party_temp = open('data/temp_party.excel', 'wb')
        by_party_web = urlopen("http://www.parliament.bg/pub/StenD/gv%s.xls" % date_string)
        by_party_temp.write(by_party_web.read())
        by_party_temp.close()
        by_party_dict = parse_excel_by_party('data/temp_party.excel')

        stenograms[ID]=stgram(date=parser.date,
                              text_lines=parser.data_list,
                              by_name_votes=by_name_dict,
                              by_party_votes=by_party_dict)

    stenograms_dump = shelve.open('data/stenograms_dump')
    stenograms_dump['stenograms'] = stenograms
    stenograms_dump.close()
