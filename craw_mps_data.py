import itertools
import os
import xml

import xmltodict

from pk_db import db, cur
from pk_logging import logging
from pk_tools import canonical_party_name

logger_mps = logging.getLogger('mps_data')

names_list = []
forces_list = []
mails_list = []
url_list = []
assembly_list = []
dob_list = []

all_mps = sorted(map(int,os.listdir('./craw_data/mp_xml')))

cur.execute("""SELECT original_url FROM elections""")
urls_already_in_db = set(_[0] for _ in cur.fetchall())

for i in all_mps:
    original_url = 'https://www.parliament.bg/bg/MP/%d'%i
    if original_url in urls_already_in_db:
        continue
    xml_file = './craw_data/mp_xml/%d'%i
    if os.path.getsize(xml_file) < 100:
        logger_mps.info("Skipping MP id %s as file is too small to contain data" % i)
        continue
    logger_mps.info("Parsing data for MP id %s" % i)
    with open(xml_file) as f:
        xml_str = f.read()
    try:
        r = xmltodict.parse(xml_str)
        name = ' '.join([r['schema']['Profile']['Names']['FirstName']['@value'],
                         r['schema']['Profile']['Names']['SirName']['@value'],
                         r['schema']['Profile']['Names']['FamilyName']['@value'],
                        ]).upper().strip()
        force = ' '.join(r['schema']['Profile']['PoliticalForce']['@value'].split(' ')[:-1])
        mail = r['schema']['Profile']['E-mail']['@value'].replace(';', ',').replace(':', ',').strip()
        dob = r['schema']['Profile']['DateOfBirth']['@value'].strip()
        assembly = r['schema']['ParliamentaryActivity']
        if assembly:
            try:
                assembly = r['schema']['ParliamentaryActivity']['ParliamentaryStructure'][0]['ParliamentaryStructureName']['@value']
            except KeyError:
                assembly = assembly['ParliamentaryStructure']['ParliamentaryStructureName']['@value']
    except xml.parsers.expat.ExpatError:
        logger_mps.warning("Parsing the xml file for MP %s failed. Trying csv."%i)
        try:
            with open('./craw_data/mp_csv/%d'%i) as csv_file:
                data = [l.strip().replace('&quot;','"').split(';')[:-1] for l in
                    csv_file.readlines()]
            name = ' '.join([d.strip() for d in data[0]])
            mail_line = [d for d in data if d and d[0].startswith('E-mail')][0]
            mail = ', '.join([d.strip() for d in mail_line[1:]])
            mail = mail.replace(';', ',').replace(':', ',')
            force_line = [d for d in data if d and d[0].startswith('Избран(а) с политическа сила')][0]
            force = ' '.join(force_line[-1].split(' ')[:-1])
            dob_line = [d for d in data if d and d[0].startswith('Дата на раждане')][0]
            dob = dob_line[1]
            assembly_i = data.index(['Парламентарна дейност'])+1
            assembly = data[assembly_i][0]
        except Exception as e:
            logger_mps.error("The csv file for MP %s is unparsable as well due to %s. Skipping this id."%(i, str(e)))
            continue
    if not (assembly or force):
        logger_mps.warning('MP %s does not contain assembly number or party information... Skipping...'%i)
        continue
    # XXX Workarounds
    # Adding missing party names
    if i in [1136, 2142,]:
        force = 'ГЕРБ'
    if name == 'ДЕНИЦА ЗЛАТКОВА ЗЛАТЕВА':
        name = 'ДЕНИЦА ЗЛАТКОВА КАРАДЖОВА'
    # XXX End of Workarounds.
    assembly = int(assembly[:2])
    try:
        force = canonical_party_name(force)
    except KeyError:
        logger_mps.error("The party name for MP %s is '%s' and does not have a canonical name."%(i, force))
    url_list.append(original_url)
    names_list.append(name)
    forces_list.append(force)
    mails_list.append([_.strip() for _ in mail.split(',')])
    assembly_list.append(assembly)
    dob_list.append(dob)

logger_mps.info('The assemblies seen in this dataset %s'%set(assembly_list))
logger_mps.info('The parties seen in this dataset %s'%set(forces_list))

# Check that names are unique in each assembly
for assembly in set(assembly_list):
    names = [n for n,a in zip(names_list,assembly_list) if a==assembly]
    if len(names)!=len(set(names)):
        logger_mps.error('In assembly %s there are name collisions' % assembly)
    else:
        logger_mps.info('No name collisions in assembly %s'%assembly)

# Check that names are unique (use date of birth to differentiate)
all_name_dob_pairs = set(zip(names_list,dob_list))
all_names = set(names_list)
if len(all_names) != len(all_name_dob_pairs):
    logger_mps.error('There are non-unique names (differentiating by date of birth): printing to STDOUT')
    print("To fix this the DB needs to be restructured to use (name,dob) as primary key.") # TODO make this DB restructuring
    print("Unique names:",len(all_names))
    print("Unique name/dob pairs:",len(all_name_dob_pairs))
    all_names_from_pairs = [n for n,s in all_name_dob_pairs]
    for n in all_names:
        if all_names_from_pairs.count(n)!=1:
            print('\n',n)
            for _n,_d in all_name_dob_pairs:
                if n==_n:
                    print(_d)
else:
    logger_mps.info('No global name collisions (differentiating by date of birth)')

# This skips old emails # TODO include old emails
dict_name_mail = dict(list(zip(names_list, mails_list)))

cur.execute("""SELECT parliament FROM parliaments""")
parliaments_already_in_db = set(_[0] for _ in cur.fetchall())
cur.executemany("""INSERT INTO parliaments VALUES (%s)""",
                [(_,) for _ in set(assembly_list)
                      if _ not in parliaments_already_in_db])

cur.execute("""SELECT party_name FROM parties""")
forces_already_in_db = set(_[0] for _ in cur.fetchall())
cur.executemany("""INSERT INTO parties VALUES (%s)""",
                [(_,) for _ in set(forces_list+['независим'])
                      if _ not in forces_already_in_db])

cur.executemany("""INSERT INTO mps VALUES (%s, %s)""",
                list(dict_name_mail.items()))

cur.executemany("""INSERT INTO elections VALUES (%s, %s, %s, %s)""",
                ((n, f, p, u)
                 for n, f, p, u
                 in zip(names_list, forces_list, assembly_list, url_list)))
db.commit()


