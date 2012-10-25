# Quick Start

 1. Install the necessary packages.
   - For postgresql run `sudo sh create_db.sh` in order to have the user and
     database installed. The `METHOD` fields of
     `/etc/postgresql/9.1/main/pg_hba.conf` should be set to `trust`.
 2. In order to craw the parliament site and generate html reports run
`sh start_over.sh`.

# Requirements

 - python (tested 2.7.2)
   - Mako (tested 0.7.2)
   - matplotlib (tested 1.1.1)
   - numpy (tested 1.6.2)
   - xlrd (tested 0.8.0)
   - xmltodict (tested 0.2)
   - psycopg2 (tested 2.4.5)
 - shell utilities (tested bash, zsh)
   - curl
   - grep
   - coreutils
 - postgresql (tested 9.1.5)

# Logging conventions
 - `warning` for stuff that must be corrected by the `parliament.bg` team, but
   which we can work around
 - `error` for stuff that is visible to our end users

# Notes

## XML file with MP information 

From http://www.parliament.bg/export.php/bg/xml/MP/xxIDxx 

```
{u'schema': {u'Bills': {u'Bill': '[---, ---]'},
             u'ParliamentaryActivity': {u'ParliamentaryStructure': '[---, ---]'},
             u'ParliamentaryControl': {u'Question': '[---, ---]'},
             u'Profile': {u'Constituency': {u'@value': '---'},
                          u'DateOfBirth': {u'@value': '---'},
                          u'E-mail': {u'@value': '---'},
                          u'Language': '---',
                          u'MaritalStatus': {u'@value': '---'},
                          u'MemberOfPreviosNA': '---',
                          u'Names': {u'FamilyName': {u'@value': '---'},
                                     u'FirstName': {u'@value': '---'},
                                     u'SirName': {u'@value': '---'}},
                          u'PlaceOfBirth': {u'@value': '---'},
                          u'PoliticalForce': {u'@value': '---'},
                          u'Profession': {u'Profession': {u'@id': '---',
                                                          u'@value': '---'}},
                          u'ScienceDegree': '---',
                          u'Website': {u'@value': '---'}},
             u'Speeches': '---'}}
```

## Todo

http://www.parliament.bg/bg/plenarysittings дава достъп то три различни
страници:

 - http://www.parliament.bg/bg/plenaryprogram - лист по година-месец от
   линкове към страници-листи с линкове към програмите за парламентарните
   събирания през въпросния месец. Въпросните страници-листи съдържат един линк
   на седмица, т.е. програмата е седмична.
 - http://www.parliament.bg/bg/plenaryst - лист по година-месец от
   линкове към страници-листи с линкове към стенограмите от парламентарните
   събирания през въпросния месец. Въпросните страници-листи съдържат няколко
   линка на седмица, т.е. линк за всяко заседание. Стенограмите от
   парламентарния контрол също са включени.
 - http://www.parliament.bg/bg/parliamentarycontrol - лист по година-месец от
   линкове към страници-листи с линкове към обобщения от парламентарните
   контроли за въпросния месец. Стенограмите не са дадени. Въпросните
   страници-листи съдържат една контрола на седмица.


Пленарни стенограми
===================

Пленарни програми
=================

TODO

Парламентарен контрол
=====================

TODO

