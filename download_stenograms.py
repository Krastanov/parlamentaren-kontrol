import random
import os.path
import re
import time

from pk_db import db, cur
from pk_logging import logging, logger_workaround
from pk_namedtuples import *
from pk_tools import urlopen, canonical_party_name, StenogramsHTMLParser

##############################################################################
# Parse and save to disc.
##############################################################################
logger_to_disk = logging.getLogger('stenograms_to_disk')

stenogram_IDs = []
assemblies_and_ids = [(7,41),(50,42),(51,43),(52,44)] # XXX Hardcoded values
for internal_id, assembly_number in assemblies_and_ids:
    stenogram_IDs += [(i, 'https://www.parliament.bg/bg/plenaryst/ns/%d/ID/'%internal_id+i)
                      for i in map(str.strip, open('craw_data/IDs_plenary_stenograms_%d'%assembly_number).readlines())]
for i, (ID, original_url) in enumerate(stenogram_IDs):
    logger_to_disk.info("Downloading stenogram %s - %d of %d." % (ID, i+1, len(stenogram_IDs)))

    try:
        filename = './craw_data/stenograms/%s.html'%ID
        if os.path.isfile(filename):
            f = open(filename)
            complete_stenogram_page = f.read()
        else:
            time.sleep(1+random.uniform(1,3))
            f = urlopen(original_url)
            complete_stenogram_page = f.read().decode('utf-8')
            assert "User validation required to continue" not in complete_stenogram_page, "We are rate limited or blocked"
            savehtml = open(filename, 'w')
            savehtml.write(complete_stenogram_page)
        parser = StenogramsHTMLParser(complete_stenogram_page)
        date_string = parser.date.strftime('%d%m%y')
    except Exception as e:
        logger_to_disk.error("Parsing problem with ID %s. %s"%(ID,str(e)))
        continue

    try:
        filename = './craw_data/stenograms/%s-%s-i.xls'%(ID,date_string)
        if not os.path.isfile(filename):
            time.sleep(1+random.uniform(1,3))
            wfilename = re.search(r"/pub/StenD/(\d*iv%s.xls[x]?)" % date_string, complete_stenogram_page).groups()[0]
            by_name_web = urlopen("https://www.parliament.bg/pub/StenD/%s" % wfilename)
            by_name_temp = open(filename, 'wb')
            by_name_temp.write(by_name_web.read())
            by_name_temp.close()
    except Exception as e:
        if parser.votes_indices:
            logger_to_disk.error("No MP name excel file was found for ID %s due to %s"%(ID,str(e)))
        else:
            logger_to_disk.info("No MP name excel file was found for ID %s because no votes happened according to stenogram."%(ID))

    try:
        filename = './craw_data/stenograms/%s-%s-g.xls'%(ID,date_string)
        if not os.path.isfile(filename):
            time.sleep(1+random.uniform(1,3))
            wfilename = re.search(r"/pub/StenD/(\d*gv%s.xls[x]?)" % date_string, complete_stenogram_page).groups()[0]
            by_party_web = urlopen("https://www.parliament.bg/pub/StenD/%s" % wfilename)
            by_party_temp = open(filename, 'wb')
            by_party_temp.write(by_party_web.read())
            by_party_temp.close()
    except Exception as e:
        if parser.votes_indices:
            logger_to_disk.error("No party excel file was found for ID %s due to %s"%(ID,str(e)))
        else:
            logger_to_disk.info("No party excel file was found for ID %s because no votes happened according to stenogram."%(ID))
