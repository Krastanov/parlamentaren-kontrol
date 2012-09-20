# -*- coding: utf-8 -*-
import urllib
import xmltodict
import xml
import re

indices = open('data/IDs_MPs').readlines()
dicts = []
forces_list = []
mails_list = []

for i in indices:
    xml_str = urllib.urlopen('http://www.parliament.bg/export.php/bg/xml/MP/'+i).read()
    try:
        r = xmltodict.parse(xml_str)
        force = r['schema']['Profile']['PoliticalForce']['@value']
        mail = r['schema']['Profile']['E-mail']['@value']
        forces_list.append(force.encode('UTF-8'))
        mails_list.append(mail.encode('UTF-8'))
    except xml.parsers.expat.ExpatError:
        pass

forces_set = set(forces_list)
mails_dict = dict(zip(mails_list, forces_list))

c = 0
for f in forces_set:
    mails = [k for k, v in mails_dict.items() if v==f]
    string = ', '.join(m.strip() for m in mails)
    string = re.sub(';', ', ', string)
    string = re.sub(':', ', ', string)
    dump = open('data/mail_dump%d'%c, 'w')
    dump.write(f)
    dump.write('\n')
    dump.write(string)
    dump.close()
    c += 1

