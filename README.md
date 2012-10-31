# Quick Start

 1. Install the necessary packages.
   - For postgresql run `sudo sh create_db.sh` in order to have the user and
     database installed. The `METHOD` fields of
     `/etc/postgresql/9.1/main/pg_hba.conf` should be set to `trust`, because
     the database connections in the scripts are usually started by a user
     different than `postgre` (basically, you should have the following line:
     `local   all             all                                     trust`)
 2. In order to craw the parliament site and generate html reports run
`sh start_over.sh`.

# Requirements

 - python (tested 2.7.2)
   - Mako (tested 0.7.2)
   - matplotlib (tested 1.1.1)
   - numpy (tested 1.6.2)
   - psycopg2 (tested 2.4.5)
   - Unidecode (tested 0.04.9)
   - xlrd (tested 0.8.0)
   - xmltodict (tested 0.2)
 - shell utilities (tested bash, zsh)
   - curl
   - grep
   - coreutils
 - SQL
   - postgresql (tested 9.1.5)
   - pgxnclient (tested 1.0.3)
     - first_last_agg (tested 0.1.2) (via `pgxnclient install first_last_agg --testing`)

# Logging conventions
 - `warning` for stuff that must be corrected by the `parliament.bg` team, but
   which we can work around
 - `error` for stuff that is visible to our end users

# Notes

## Workarounds

*   The votes-by-name list for stenogram ID 2766 contains strange formatting.
Currently we use a manually modified excel file instead of the one on the
parliament website. Below is a copy of the explanation given by the
parliamentary infocenter (in Bulgarian):

    > За г-жа ВАНЯ ЧАВДАРОВА ДОБРЕВА беше допусната грешка при първоначлното
въвеждане на данни за нея и след поправяне на грешката системата дава следващ
идентификационен номер.

*   The MPs with names 'МИХАИЛ ВЛАДИМИРОВ ВЛАДОВ' and 'НИКОЛАЙ НАНКОВ НАНКОВ'
have never been present in a voting session, however are registered for a
number of them. At the same time they are not in the MPs list, so trying to
import their absences in the data base gives a foreign key violation. We just
skip them. Below is a copy of the explanation given by the parliamentary
infocenter (in Bulgarian):

    > За г-жа ВАНЯ ЧАВДАРОВА ДОБРЕВА беше допусната грешка при първоначлното
въвеждане на данни за нея и след поправяне на грешката системата дава следващ
идентификационен номер.

*   The MP name "МАРИЯНА ПЕТРОВА ИВАНОВА-НИКОЛОВА" is a misspell of "МАРИАНА
ПЕТРОВА ИВАНОВА-НИКОЛОВА". Below is a copy of the explanation given by the
parliamentary infocenter (in Bulgarian):

    > Госпожа Мариана Иванова – Николова е избрана за народен представител с >
решение на Централната избирателна комисия №2041-НС, съобщено в пленарна > зала
на 03.10.2012 г. с името МАРИЯНА ПЕТРОВА ИВАНОВА – НИКОЛОВА.  С така > изписано
име госпожа Иванова- Николова е въведена в системата за > гласуване. Само и
единствено Централната избирателна комисия може да > промени изписването на
името на народен представител. Такава промяна е > извършена от тях с решение
№2047-МИ,съобщено в пленарна зала на > 10.10.2012 г. за поправка на явна
фактическа грешка в името на народният > представител Мариана Петрова
Иванова-Николова, вместо „МАРИЯНА” да се > чете ”МАРИАНА”. Именно поради тази
причина, а не допусната от нас > правописна грешка госпожа Иванова-Николова
фигурира в посочените от Вас > разпечатки от поименно гласуване, като
„МАРИЯНА".

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
