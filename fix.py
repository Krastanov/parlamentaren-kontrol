# -*- coding: utf-8 -*-
import xml

import xmltodict

from pk_db import db, cur
from pk_logging import logging
from pk_tools import urlopen, canonical_party_name


indices = map(int, open('data/IDs_MPs').readlines())
cur.execute("""SELECT * FROM mps""")
mps = cur.fetchall()
for mp in mps:
    print u'-----'.join(map(unicode, mp))
    original_url = unicode('http://www.parliament.bg/bg/MP/'+mp[-1].split('/')[-1])
    cur.execute("""UPDATE mps SET original_url = %s WHERE mp_name = %s""",
            (original_url, mp[0]))
    print mp[-1].split('/')[-1]
db.commit()
