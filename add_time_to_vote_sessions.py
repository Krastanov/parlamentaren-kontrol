# -*- coding: utf-8 -*-
import psycopg2
from datetime import datetime

# Return unicode instead of 'UTF-8' encoded str
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

db = psycopg2.connect(database="parlamentarenkontrol", user="parlamentarenkontrol")
cur = db.cursor(name='blah')
ccur = db.cursor()
ucur = db.cursor()

ccur.execute("""SELECT COUNT(*) FROM vote_sessions""")
count = ccur.fetchall()[0][0]
c = 1
cur.execute("""SELECT * FROM vote_sessions""")
for (st_date, ses_nb, descr, time) in cur:
    print st_date, ses_nb, '-', c, 'of', count
    c += 1
    unpr_time, unpr_descr = descr.split(u'по тема')
    new_time = datetime.strptime(unpr_time[-6:], '%H:%M ')
    new_descr = unpr_descr.strip()
    assert len(new_descr) > 10
    ucur.execute("""UPDATE vote_sessions
                    SET description = %s, time = %s
                    WHERE stenogram_date = %s AND session_number = %s""",
                    (new_descr, new_time, st_date, ses_nb))

db.commit()
