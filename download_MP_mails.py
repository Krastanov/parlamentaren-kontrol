# -*- coding: utf-8 -*-
import urllib
import xmltodict
import xml
import re


def canonical_party_name(name):
    party_dict = {
        u'Партия "Атака"': u'АТАКА' ,
        u'ДПС "Движение за права и свободи"': u'ДПС',
        u'"Синята коалиция"': u'СК',
        u'"Коалиция за България"': u'КБ',
        u'"Ред, законност и справедливост"': u'РЗС',
        u'НЕЗ': u'независим',
    }
    return party_dict.get(name, name)


if __name__ == '__main__':
    indices = map(int, open('data/IDs_MPs').readlines())
    dicts = []
    names_list = []
    forces_list = []
    mails_list = []

    #TODO hardcoded value: id of the first mp from the current assembly
    for i in range(835, max(indices)+1):
        xml_str = urllib.urlopen('http://www.parliament.bg/export.php/bg/xml/MP/%d'%i).read()
        try:
            print i
            r = xmltodict.parse(xml_str)
            name = ' '.join([
                            r['schema']['Profile']['Names']['FirstName']['@value'],
                            r['schema']['Profile']['Names']['SirName']['@value'],
                            r['schema']['Profile']['Names']['FamilyName']['@value'],
                            ]).encode('UTF-8').upper().strip()
            force = ' '.join(r['schema']['Profile']['PoliticalForce']['@value'].split(' ')[:-1])
            force = canonical_party_name(force).encode('UTF-8')
            mail = r['schema']['Profile']['E-mail']['@value'].encode('UTF-8')
            mail = re.sub(';', ', ', mail)
            mail = re.sub(':', ', ', mail).strip()
            names_list.append(name)
            forces_list.append(force)
            mails_list.append(mail)
        except xml.parsers.expat.ExpatError:
            try:
                csv_file = urllib.urlopen('http://www.parliament.bg/export.php/bg/csv/MP/%d'%i)
                print "WTF, TODO" #TODO
                data = [l.strip().replace('&quot;','"').split(';')[:-1] for l in csv_file.readlines()]
                name = ' '.join([d.strip() for d in data[0]])
                mail = ', '.join([d.strip() for d in data[9]])
                mail = re.sub(';', ', ', mail)
                mail = re.sub(':', ', ', mail).strip()
                force = d[6][-1]
                force = canonical_party_name(force).encode('UTF-8')
                names_list.append(name)
                forces_list.append(force)
                mails_list.append(mail)
            except Exception:
                print "DOUBLE WTF"
                print i

    forces_set = set(forces_list)
    mails_dict = dict(zip(mails_list, forces_list))

    import psycopg2
    db = psycopg2.connect(database="parlamentarenkontrol", user="parlamentarenkontrol")
    cur = db.cursor()
    cur.executemany("""INSERT INTO parties VALUES (%s)""", zip(sorted(forces_set)+[u'независим']))
    cur.executemany("""INSERT INTO mps VALUES (%s, %s, %s)""", zip(names_list, forces_list, mails_list))
    db.commit()

    c = 0
    for f in forces_set:
        mails = [k for k, v in mails_dict.items() if v==f]
        string = ', '.join(m.strip() for m in mails)
        dump = open('data/mail_dump%d'%c, 'w')
        dump.write(f)
        dump.write('\n')
        dump.write(string)
        dump.close()
        c += 1

