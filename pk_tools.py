# -*- coding: utf-8 -*-
import urllib2


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
