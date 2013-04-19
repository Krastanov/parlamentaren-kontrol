# -*- coding: utf-8 -*-
import xml

import xmltodict

from pk_db import db, cur
from pk_logging import logging
from pk_tools import urlopen, canonical_party_name


logger_mps = logging.getLogger('mps_data')


names_list = []
forces_list = []
mails_list = []
url_list = []


#TODO hardcoded value: id of the first mp from the current assembly
indices = map(int, open('data/IDs_MPs').readlines())
cur.execute("""SELECT original_url FROM mps""")
urls_already_in_db = set(zip(*cur.fetchall())[0])
for i in range(835, max(indices)+1):
    original_url = unicode('http://www.parliament.bg/bg/MP/%d'%i)
    if original_url in urls_already_in_db:
        continue
    logger_mps.info("Parsing data for MP id %s" % i)
    xml_file = unicode('http://www.parliament.bg/export.php/bg/xml/MP/%d'%i)
    xml_str = urlopen(xml_file).read()
    try:
        r = xmltodict.parse(xml_str)
        name = ' '.join([r['schema']['Profile']['Names']['FirstName']['@value'],
                         r['schema']['Profile']['Names']['SirName']['@value'],
                         r['schema']['Profile']['Names']['FamilyName']['@value'],
                        ]).encode('UTF-8').upper().strip()
        force = ' '.join(r['schema']['Profile']['PoliticalForce']['@value'].split(' ')[:-1])
        force = canonical_party_name(force).encode('UTF-8')
        mail = r['schema']['Profile']['E-mail']['@value'].encode('UTF-8').replace(';', ',').replace(':', ',').strip()
    except xml.parsers.expat.ExpatError:
        logger_mps.warning("Parsing the xml file for MP %s failed. Trying csv."%i)
        try:
            csv_file = urlopen('http://www.parliament.bg/export.php/bg/csv/MP/%d'%i)
            data = [l.strip().replace('&quot;','"').split(';')[:-1] for l in csv_file.readlines()]
            name = ' '.join([d.strip() for d in data[0]])
            mail = ', '.join([d.strip() for d in data[9][1:]])
            mail = mail.replace(';', ',').replace(':', ',')
            force = ' '.join(data[6][-1].decode('UTF-8').split(' ')[:-1])
            force = canonical_party_name(force).encode('UTF-8')
        except Exception, e:
            logger_mps.error("The csv file for MP %s is unparsable as well due to %s. Skipping this id."%(i, str(e)))
            continue
    url_list.append(original_url)
    names_list.append(name)
    forces_list.append(force)
    mails_list.append(mail)


cur.executemany("""INSERT INTO parties VALUES (%s)""",
                zip(list(set(forces_list))+[u'независим']))
cur.executemany("""INSERT INTO mps VALUES (%s, %s, %s, %s)""",
                zip(names_list, forces_list, mails_list, url_list))
db.commit()
