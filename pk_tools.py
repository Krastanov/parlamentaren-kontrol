# -*- coding: utf-8 -*-
import re
import urllib2
import unidecode as _unidecode

from pk_db import db


def urlopen(url, retry=3):
    """``urllib2.urlopen`` with retry"""
    for i in range(retry):
        try:
            return urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            pass
    raise e


def canonical_party_name(name):
    """Gives a canonical name for a party."""
    party_dict = {
        # for the xml parser
        u'Партия "Атака"': u'АТАКА' ,
        u'ДПС "Движение за права и свободи"': u'ДПС',
        u'"Синята коалиция"': u'СК',
        u'"Коалиция за България"': u'КБ',
        u'"Ред, законност и справедливост"': u'РЗС',
        # for the excel parser
        u'НЕЗ': u'независим',
    }
    return party_dict.get(name, name)


def unidecode(string):
    """Transliterate unicode to latin."""
    return _unidecode.unidecode(string.replace(u'ѝ',u'и')
                                      .replace(u'ъ',u'а').replace(u'Ъ',u'А')
                                      .replace(u'ь',u'й').replace(u'Ь',u'Й'))


def unicode2urlsafe(string):
    return unidecode(string).replace(' ', '_').lower()


mpscur = db.cursor()
mpscur.execute("""SELECT mp_name FROM mps""")
names = [n[0] for n in mpscur]
full_names = [re.compile(n, flags=re.I|re.U) for n in names]
first_last_names = [re.compile(' '.join(n.split()[::2]), flags=re.I|re.U) for n in names]
last_names = [re.compile(n.split()[-1], flags=re.I|re.U) for n in names]
def annotate_mps(html_lines):
    #print map(len, map(set, [full_names, first_last_names, last_names]))
    return ([len(list(cre.finditer(''.join(html_lines)))) for cre in full_names],
       [len(list(cre.finditer(''.join(html_lines)))) for cre in first_last_names],
       [len(list(cre.finditer(''.join(html_lines)))) for cre in last_names])
