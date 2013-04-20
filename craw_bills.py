# -*- coding: utf-8 -*-
import datetime
import re

import bs4

from pk_db import db
from pk_logging import logging
from pk_tools import urlopen

state_of_bill_dict = {
u'внесен(зала първо четене)':                          'proposed_1st',
u'внесен(зала второ четене)':                          'proposed_2nd',
u'приет(зала първо четене)':                           'accepted_1st',
u'приет(зала второ четене)':                           'accepted_2nd',
u'отхвърлен(зала първо четене)':                       'rejected_1st',
u'отхвърлен(зала второ четене)':                       'rejected_2nd',
u'оттеглен от вносителя(оттеглен)':                    'retracted',
u'наложено вето(вето президент)':                      'vetoed',
u'внесен(преразглеждане зала (след вето))':            'proposed_after_veto',
u'повторно приемане(преразглеждане зала (след вето))': 'accepted_after_veto',
# TODO the next few are unclear in their definition (raise a warning)
u'оспорени текстове(преразглеждане зала (след вето))': 'challenged_after_veto',
u'оспорен по принцип(преразглеждане зала (след вето))':'challenged_after_veto',
#u'обсъждане(зала първо четене)':                       'proposed_1st', see signature 002-02-50
}
##############################################################################
# Gather bills.
##############################################################################
logger_html_bills = logging.getLogger('html_parser_bills')

origurlcur = db.cursor()
origurlcur.execute("""SELECT original_url FROM bills""")
urls_already_in_db = set(u[0] for u in origurlcur)

logger_html_bills.info('Opening calendar.')
base_url = 'http://www.parliament.bg'
parser_calendar = bs4.BeautifulSoup(urlopen(base_url + '/bg/bills/').read())
for month in parser_calendar.find('div', id='calendar').find_all('a'):
    href = month.get('href')
    y,m = map(int, href.split('/')[-1].split('-'))
    if y<2009 or (y==2009 and m<7): continue # XXX hardcoded check (only last parliament)
    logger_html_bills.info('Opening calendar %d %d.'%(y, m))
    month_page = bs4.BeautifulSoup(urlopen(base_url + href).read())
    for a in month_page.find('div', id='monthview').find_all('a'):
        original_url = base_url + a.get('href')
        if original_url in urls_already_in_db:
            continue
        bill_page = bs4.BeautifulSoup(urlopen(original_url).read())
        table = bill_page.find('table', class_='bills')

        name = table.find_all('tr')[0].find('strong').string.split(u'Законопроект за')[-1].strip()
        sig = table.find_all('tr')[1].find_all('td')[1].string.strip()
        date = datetime.datetime.strptime(table.find_all('tr')[2].find_all('td')[1].string.strip(), '%d/%m/%Y')
        if date<datetime.datetime(2009, 7, 21): continue # XXX hardcoded check (only last parliament)
        authors = [a.string.strip() for a in table.find_all('tr')[5].find_all('a')]
        chronology = [li.string.strip() for li in table.find_all('tr')[8].find_all('li')]

        billcur = db.cursor()
        billcur.execute("""INSERT INTO bills VALUES (%s, %s, %s, %s)""",
                        (name, sig, date, original_url))
        for auth in authors:
            if auth == u'Министерски съвет':
                billcur.execute("""INSERT INTO bills_by_government VALUES (%s)""", (sig,))
                continue
            billcur.execute("""INSERT INTO bill_authors VALUES (%s, %s)""", (sig, auth))
        for event in set(chronology):
            # XXX a set because there are errors of repetition in the original
            # TODO raise a warning
            ev_date_str, descr = [s.strip() for s in event.split('-')]
            if descr == u'обсъждане(зала първо четене)': continue #TODO see 002-02-50
            ev_date = datetime.datetime.strptime(ev_date_str, '%d/%m/%Y')
            billcur.execute("""INSERT INTO bill_history VALUES (%s, %s, %s)""",
                            (sig, ev_date, state_of_bill_dict[descr]))
        db.commit()
