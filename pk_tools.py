# -*- coding: utf-8 -*-
import itertools
import re
import urllib.request, urllib.error, urllib.parse
import unidecode as _unidecode

from pk_db import db

groupby_list = lambda l, kf: [(k, list(v)) for k, v in itertools.groupby(l, kf)]
sortgroupby_list = lambda l, kf: groupby_list(sorted(l, key=kf), kf)

def urlopen(url, retry=3):
    """``urllib2.urlopen`` with retry"""
    for i in range(retry):
        try:
            return urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            pass
    raise e


def canonical_party_name(name):
    """Gives a canonical name for a party."""
    party_dict = {
        # for the xml parser
        'Партия "Атака"'                   : 'АТАКА',
        'ПП „Атака“'                       : 'АТАКА',
        'ПП „ГЕРБ“'                        : 'ГЕРБ',
        'ДПС "Движение за права и свободи"': 'ДПС',
        'ПП „Движение за права и свободи“' : 'ДПС',
        '"Синята коалиция"'                : 'СК',
        '"Коалиция за България"'           : 'КБ',
        'КП „Коалиция за България“'        : 'КБ',
        '"Ред, законност и справедливост"' : 'РЗС',
        # for the excel parser
        'НЕЗ': 'независим',
    }
    return party_dict.get(name, name)


def unidecode(string):
    """Transliterate unicode to latin."""
    return _unidecode.unidecode(string.replace('ѝ','и')
                                      .replace('ъ','а').replace('Ъ','А')
                                      .replace('ь','й').replace('Ь','Й'))


def unicode2urlsafe(string):
    return unidecode(string).replace(' ', '_').lower()


mpscur = db.cursor()
mpscur.execute("""SELECT mp_name FROM mps ORDER BY mp_name""")
names = [n[0] for n in mpscur]
links = ["mp_%s.html"%unicode2urlsafe(n) for n in names]
fl_names = [' '.join(n.split()[::2]) for n in names]
l_names = [n.split()[-1] for n in names]

names_links    = sortgroupby_list(list(zip(   names,names,links)), lambda _:_[0])
fl_names_links = sortgroupby_list(list(zip(fl_names,names,links)), lambda _:_[0])
l_names_links  = sortgroupby_list(list(zip( l_names,names,links)), lambda _:_[0])

permited_separators =  '=[.,?!:; ()]'
re1 = '(?<{s}){k}(?{s})'
re2 =       '^{k}(?{s})'
re3 = '(?<{s}){k}$'
re4 =       '^{k}$'
base_re = ('(%s|%s|%s|%s)(?!=&nbsp;)'%(re1, re2, re3, re4)).format(s=permited_separators, k='{k}')

escape_spaces = lambda n: n.replace(' ', '&nbsp;')

key_re_a_div = [(key,
                 re.compile(base_re.format(k=key), flags=re.I|re.U|re.M),
                 '<a href="#" class="tooltip" data-content="#mp_%s" data-action="click">%s</a>'%(
                     unicode2urlsafe(key), escape_spaces(key))
                   if len(knls)>1 else '<a href="%s">%s</a>'%(knls[0][2], escape_spaces(key)),
                 '<div class="tooltip-content" id="mp_%s">%s</div>'%(
                     unicode2urlsafe(key),
                     '<ul>%s</ul>'%(''.join('<li><a href="%s">%s</a></li>'%(link,name)
                                            for key_,name,link in knls)))
                   if len(knls)>1 else '')
                for key, knls
                in names_links + fl_names_links + l_names_links]

def annotate_mps(html_text):
    divs = set()
    for key, rexp, a, div in key_re_a_div:
        html_text, n = rexp.subn(a, html_text)
        if n:
            divs.add(div)
    return html_text, divs
