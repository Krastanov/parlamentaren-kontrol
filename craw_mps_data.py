# -*- coding: utf-8 -*-

import itertools
import os
import xml

import xmltodict

from pk_db import db, cur
from pk_logging import logging
from pk_tools import urlopen, canonical_party_name


logger_mps = logging.getLogger('mps_data')

names_list = []
forces_list = []
mails_list = []
url_list = []


# MPs from the current parliament. Some MPs might be missing from the
# `.../bg/MP` list if they are not active anymore, hence the use of `range`.
# Contains invalid IDs as well. To diminish the amount of invalid IDs the known
# IDs are hardcoded, but this is not necessary for the crawler to work. The use
# of `range(..., last+1)` ensures that any new IDs will also be crawled.
new_mps = [
1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452,
1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465,
1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 1474, 1475, 1476, 1477, 1478,
1479, 1480, 1481, 1482, 1482, 1483, 1484, 1485, 1486, 1487, 1488, 1489, 1490,
1491, 1492, 1493, 1494, 1495, 1495, 1496, 1497, 1498, 1499, 1500, 1501, 1502,
1503, 1504, 1505, 1506, 1507, 1508, 1509, 1510, 1510, 1511, 1512, 1513, 1514,
1515, 1515, 1516, 1517, 1518, 1519, 1520, 1521, 1522, 1523, 1524, 1525, 1526,
1527, 1528, 1529, 1530, 1531, 1532, 1533, 1534, 1535, 1536, 1537, 1538, 1539,
1540, 1541, 1542, 1543, 1544, 1545, 1546, 1547, 1548, 1549, 1550, 1551, 1552,
1553, 1554, 1555, 1556, 1557, 1558, 1559, 1560, 1561, 1562, 1563, 1564, 1565,
1566, 1567, 1568, 1569, 1570, 1571, 1572, 1573, 1574, 1575, 1576, 1577, 1578,
1579, 1580, 1581, 1582, 1583, 1584, 1585, 1585, 1586, 1587, 1588, 1589, 1590,
1591, 1592, 1593, 1593, 1594, 1595, 1596, 1597, 1598, 1599, 1600, 1601, 1602,
1603, 1604, 1605, 1605, 1606, 1607, 1608, 1609, 1610, 1611, 1612, 1613, 1614,
1615, 1616, 1616, 1617, 1618, 1619, 1620, 1621, 1622, 1623, 1624, 1625, 1626,
1627, 1628, 1629, 1630, 1631, 1632, 1632, 1633, 1634, 1635, 1635, 1636, 1637,
1638, 1639, 1660, 1661, 1662, 1663, 1664, 1665, 1666, 1667, 1668, 1669, 1670,
1671, 1672, 1673, 1674, 1675, 1676, 1677, 1678, 1679, 1680, 1681, 1682, 1683,
1684, 1685, 1686, 1687, 1688, 1689, 1690, 1691, 1692, 1693, 1694, 1695, 1696,
1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709,
1727, 1728, 1729, 1730, 1732, 1733, 1734]
com = """curl https://www.parliament.bg/bg/MP 2> /dev/null | grep ">Информация" | grep -o '[0-9]*' | sort -n | """
new_mps = [int(_.strip()) for _ in os.popen(com+"cat","r").readlines()]
first, last = min(new_mps), max(new_mps)
new_mps += list(range(new_mps[-1]+1, last+1))
# Preprocessed list of MPs from previous parliaments. (There is no fast way to
# get this from the website). `range(835, last+1)` will work as well but there
# are many invalid ids that are just a waste of time to craw.
old_mps = [
835, 836, 837, 838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850,
851, 852, 853, 854, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866,
867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881, 882,
883, 884, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898,
899, 900, 901, 902, 903, 904, 905, 906, 907, 908, 909, 910, 911, 912, 913, 914,
915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 930,
931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946,
947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 960, 961, 962,
963, 964, 965, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978,
979, 980, 981, 982, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 993, 994,
995, 996, 997, 998, 999, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008,
1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021,
1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034,
1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047,
1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060,
1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1069, 1070, 1071, 1072, 1073,
1074, 1075, 1076, 1077, 1078, 1079, 1080, 1081, 1082, 1083, 1084, 1085, 1086,
1087, 1088, 1089, 1108, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119, 1120,
1122, 1123, 1124, 1127, 1128, 1129, 1130, 1131, 1132, 1133, 1134, 1135, 1136,
1137, 1138]
all_mps = old_mps + new_mps
border_id = old_mps[-1]+1


cur.execute("""SELECT original_url FROM elections""")
urls_already_in_db = set(_[0] for _ in cur.fetchall())
for i in all_mps:
    original_url = 'https://www.parliament.bg/bg/MP/%d'%i
    if original_url in urls_already_in_db:
        continue
    logger_mps.info("Parsing data for MP id %s" % i)
    xml_file = 'https://www.parliament.bg/export.php/bg/xml/MP/%d'%i
    xml_str = urlopen(xml_file).read()
    try:
        r = xmltodict.parse(xml_str)
        name = ' '.join([r['schema']['Profile']['Names']['FirstName']['@value'],
                         r['schema']['Profile']['Names']['SirName']['@value'],
                         r['schema']['Profile']['Names']['FamilyName']['@value'],
                        ]).upper().strip()
        force = ' '.join(r['schema']['Profile']['PoliticalForce']['@value'].split(' ')[:-1])
        mail = r['schema']['Profile']['E-mail']['@value'].replace(';', ',').replace(':', ',').strip()
    except xml.parsers.expat.ExpatError:
        logger_mps.warning("Parsing the xml file for MP %s failed. Trying csv."%i)
        try:
            csv_file = urlopen('https://www.parliament.bg/export.php/bg/csv/MP/%d'%i)
            data = [l.decode('utf-8').strip().replace('&quot;','"').split(';')[:-1] for l in
                    csv_file.readlines()]
            name = ' '.join([d.strip() for d in data[0]])
            mail = ', '.join([d.strip() for d in data[9][1:]])
            mail = mail.replace(';', ',').replace(':', ',')
            force = ' '.join(data[6][-1].split(' ')[:-1])
        except Exception as e:
            logger_mps.error("The csv file for MP %s is unparsable as well due to %s. Skipping this id."%(i, str(e)))
            continue
    url_list.append(original_url)
    names_list.append(name)
    forces_list.append(force)
    mails_list.append(mail)


forces_list = [canonical_party_name(_) for _ in forces_list]
mails_list = [[__.strip() for __ in _.split(',')] for _ in mails_list]
dict_name_mail = dict(list(zip(names_list, mails_list)))


cur.execute("""SELECT party_name FROM parties""")
forces_already_in_db = set(_[0] for _ in cur.fetchall())
cur.executemany("""INSERT INTO parties VALUES (%s)""",
                [(_,) for _ in set(forces_list+['независим'])
                      if _ not in forces_already_in_db])
cur.executemany("""INSERT INTO mps VALUES (%s, %s)""",
                list(dict_name_mail.items()))
cur.executemany("""INSERT INTO elections VALUES (%s, %s, %s, %s)""",
                ((n, f, 41 if int(u.split('/')[-1]) < border_id else 42, u)
                 for n, f, u in zip(names_list, forces_list, url_list)))
db.commit()


problematic = []
s = sorted(zip(names_list,forces_list,url_list), key=lambda _:_[0])
sn = zip(*s)[0] if names_list else []
c = 3
for _ in set(names_list):
    if name.count(_) == c:
        i = sn.index(_)
        for j in range(c):
            problematic.append(s[i+j])
c = 4
for _ in set(names_list):
    if name.count(_) == c:
        i = sn.index(_)
        for j in range(c):
            problematic.append(s[i+j])
c = 5
for _ in set(names_list):
    if name.count(_) >= c:
        i = sn.index(_)
        for j in range(c):
            problematic.append(s[i+j])
c = 2
for _ in set(names_list):
    if name.count(_) >= c:
        i = sn.index(_)
        if s[i+1][1] != s[i][1]:
            problematic.append(s[i])
            problematic.append(s[i+1])
if problematic:
    logger_mps.error("There are repeated names that are either misformated"
                     " profiles or two different representatives sharing the"
                     " same name. The full list is shown on STDOUT.")
    for p in problematic:
        print(*p)
else:
    logger_mps.info("No problems with repeated names detected.")
