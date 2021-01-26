# -*- coding: utf-8 -*-
import datetime
import itertools
import re
import urllib.request, urllib.error, urllib.parse

import bs4
import unidecode as _unidecode

from pk_db import db

groupby_list = lambda l, kf: [(k, list(v)) for k, v in itertools.groupby(l, kf)]
sortgroupby_list = lambda l, kf: groupby_list(sorted(l, key=kf), kf)

def urlopen(url, retry=3):
    """``urllib2.urlopen`` with retry"""
    error = None
    for i in range(retry):
        try:
            opener = urllib.request.build_opener()
            opener.addheader = [('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0')]
            return opener.open(url)
        except urllib.error.HTTPError as e:
            error = e
    raise error


party_dict = {
    # for the xml MP parser, based on the names seen in the xls stenograms
    'Коалиция АБВ - (Алтернатива за българско възраждане)' : 'АБВ',
    'Партия "Атака"'                           : 'АТАКА',
    'ПП „Атака“'                               : 'АТАКА',
    'ПП "Атака"'                               : 'АТАКА',
    'Коалиция "Атака"'                         : 'АТАКА',
    'КП БЪЛГАРИЯ БЕЗ ЦЕНЗУРА'                  : 'ББЦ',
    'ББЦ'                                      : 'ББЦ',
    'БДЦ'                                      : 'БДЦ',
    'БДЦНС'                                    : 'БДЦНС',
    'БСП'                                      : 'БСП',
    'БСП за БЪЛГАРИЯ'                          : 'БСПЗБ',
    'ПГБСП'                                    : 'БСПЗБ',
    'БСП лява България'                        : 'БСПЛБ',
    'БСПЛБ'                                    : 'БСПЛБ',
    'ВОЛЯ'                                     : 'ВОЛЯ',
    'ПП ГЕРБ'                                  : 'ГЕРБ',
    'ПП „ГЕРБ“'                                : 'ГЕРБ',
    'ПП "ГЕРБ"'                                : 'ГЕРБ',
    'ДПС "Движение за права и свободи"'        : 'ДПС',
    'ПП „Движение за права и свободи“'         : 'ДПС',
    '"Движение за права и свободи"'            : 'ДПС',
    'Движение за права и свободи - ДПС'        : 'ДПС',
    'ДПС (ДПС – Либерален съюз – Евророма)'    : 'ДПС',
    'ДПС - Движение за права и свободи'        : 'ДПС',
    'ПП "Движение за права и свободи"'         : 'ДПС',
    '"Коалиция за България"'                   : 'КБ',
    'КП „Коалиция за България“'                : 'КБ',
    'КП "Коалиция за България"'                : 'КБ',
    'ОБЕДИНЕНИ ПАТРИОТИ - НФСБ, АТАКА и ВМРО'  : 'ОП',
    'ПАТРИОТИЧЕН ФРОНТ - НФСБ и ВМРО'          : 'ПФ',
    'РЕФОРМАТОРСКИ БЛОК - БЗНС, ДБГ, ДСБ, НПСД, СДС' : 'РБ',
    '"Ред, законност и справедливост"'         : 'РЗС',
    '"Синята коалиция"'                        : 'СК',

    # These are not present in XLS stenograms
    'Коалиция "Български Народен Съюз"'        : 'БНС',
    '"Демократи за Силна България"'            : 'ДСБ',
    'Коалиция "Обединени Демократични Сили"'   : 'ОДС',
    '"Обединени демократични сили – СДС, Народен съюз: БЗНС-Народен съюз и Демократическа партия, БСДП, Национално ДПС"' : 'ОДС',
    '"Национално движение Симеон Втори"'       : 'НДСВ',

    'НЕЗ': 'независим',
}
party_dict.update(dict(zip(party_dict.values(),party_dict.values())))
def canonical_party_name(name):
    """Gives a canonical name for a party."""
    return party_dict[name]


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

##############################################################################
# HTML Parsing
##############################################################################
class StenogramsHTMLParser(bs4.BeautifulSoup):
    def __init__(self, text):
        super(StenogramsHTMLParser, self).__init__(text, 'html.parser')

        self.date = datetime.datetime.strptime(self.find('div', class_='dateclass').string.strip(), '%d/%m/%Y')

        self.data_list = list(self.find('div', class_='markcontent').stripped_strings)

        self.votes_indices = []
        how_many_have_voted_marker = 'Гласувал[и]?[ ]*\d*[ ]*народни[ ]*представители:'
        # The above marker regex must permit a number of spelling errors that can be present in the stenograms.
        for i, l in enumerate(self.data_list):
            if re.search(how_many_have_voted_marker, l):
                self.votes_indices.append(i)

