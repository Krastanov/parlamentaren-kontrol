import datetime
import re

import bs4
import xlrd

from pk_db import db, cur
from pk_logging import logging, logger_workaround
from pk_namedtuples import *
from pk_tools import urlopen, canonical_party_name


##############################################################################
# HTML Parsing
##############################################################################
class StenogramsHTMLParser(bs4.BeautifulSoup):
    def __init__(self, text):
        super(StenogramsHTMLParser, self).__init__(text)

        self.date = datetime.datetime.strptime(self.find('div', class_='dateclass').string.strip(), '%d/%m/%Y')

        self.data_list = list(self.find('div', class_='markcontent').stripped_strings)

        self.votes_indices = []
        how_many_have_voted_marker = 'Гласувал[и]?[ ]*\d*[ ]*народни[ ]*представители:'
        # The above marker regex must permit a number of spelling errors that can be present in the stenograms.
        for i, l in enumerate(self.data_list):
            if re.search(how_many_have_voted_marker, l):
                self.votes_indices.append(i)

##############################################################################
# Parse and save to disc.
##############################################################################
logger_to_db = logging.getLogger('to_db')

stenogram_IDs = []
assemblies_and_ids = [(7,41),(50,42),(51,43),(52,44)] # XXX Hardcoded values
for internal_id, assembly_number in assemblies_and_ids:
    stenogram_IDs += [(i, 'https://www.parliament.bg/bg/plenaryst/ns/$d/ID/'%internal_id+i)
                      for i in map(str.strip, open('craw_data/IDs_plenary_stenograms_%d'%assembly_number).readlines())]
for i, (ID, original_url) in enumerate(stenogram_IDs[-5:]):
    logger_to_db.info("Downloading stenogram %s - %d of %d." % (ID, i+1, len(stenogram_IDs)))

    try:
        f = urlopen(original_url)
        complete_stenogram_page = f.read().decode('utf-8')
        parser = StenogramsHTMLParser(complete_stenogram_page)
        date_string = parser.date.strftime('%d%m%y')
    except Exception as e:
        logger_to_db.error("Parsing problem with ID %s. %s"%(ID,str(e)))
        continue


    try:
        filename = re.search(r"/pub/StenD/(\d*iv%s.xls)" % date_string, complete_stenogram_page).groups()[0]
        by_name_web = urlopen("https://www.parliament.bg/pub/StenD/%s" % filename)
        by_name_temp = open('./craw_data/%s-i.xls'%date_string, 'wb')
        by_name_temp.write(by_name_web.read())
        by_name_temp.close()
    except Exception as e:
        logger_to_db.error("No MP name excel file was found for ID %s due to %s"%(ID,str(e)))

    try:
        filename = re.search(r"/pub/StenD/(\d*gv%s.xls)" % date_string, complete_stenogram_page).groups()[0]
        by_party_web = urlopen("https://www.parliament.bg/pub/StenD/%s" % filename)
        by_party_temp = open('./craw_data/%s-g.xls'%date_string, 'wb')
        by_party_temp.write(by_party_web.read())
        by_party_temp.close()
    except Exception as e:
        logger_to_db.error("No party excel file was found for ID %s due to %s"%(ID,str(e)))
