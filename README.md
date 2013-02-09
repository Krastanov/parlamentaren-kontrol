# Quick Start

 1. Install the necessary packages.
 2. Set up postgres user permissions. Run
    `echo "createuser parlamentarenkontrol -s" | sudo su postgres` in order to
    have the database user set up. Then the `METHOD` fields of
    `/etc/postgresql/9.1/main/pg_hba.conf` should be set to `trust`, because
    the database connections in the scripts are usually started by a user
    different than `postgres` (basically, you should have the following line:
    `local   all   all   trust`)
 3. Matplotlib needs certain fonts to be installed. On linux make sure that
    `/usr/share/fonts/truetype/freefont` is present (and update the font cache)
    or just `apt-get install fonts-freefont-ttf ` on debian. You may need to
    remove font caches from the `.matplotlib` directory.
 4. In order to set up the database, craw the parliament site and generate html
    reports run `sh start_over.sh`.

Remark: Be sure to have correctly set your locales to UTF8, otherwise much of
the code could fail. To check the locales of your DB you can look at `psql -l`.

# Requirements

 - python (tested 2.7.2)
   - beautifulsoup4 (tested 4.1.3)
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

 - `warning` for stuff that could be corrected by the `parliament.bg` team, but
   which we can also work around
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
    import their absences in the data base gives a foreign key violation. We
    just skip them. Below is a copy of the explanation given by the
    parliamentary infocenter (in Bulgarian):

    > Здравейте, г-н МИХАИЛ ВЛАДИМИРОВ ВЛАДОВ и г-н НИКОЛАЙ НАНКОВ НАНКОВ са
били избрани за народни представители с Решение на ЦИК, но не са встъпвали в
длъжност. По тази причина фигурират като имена в разпечатките до момента, в
който ЦИК излезе с Решение, в което обявява за избран следващия народен
представител в листата на съответната партия.

*   The MP name "МАРИЯНА ПЕТРОВА ИВАНОВА-НИКОЛОВА" is a misspell of "МАРИАНА
    ПЕТРОВА ИВАНОВА-НИКОЛОВА". It is present in stenograms 2809, 2810, 2811, 2812.
    Below is a copy of the explanation given by the parliamentary infocenter (in
    Bulgarian):

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

*   The MP name "ВЕНЦЕСЛАВ ВАСИЛЕВ ВЪРБАНОВ" is a misspell of "ВЕНЦИСЛАВ
    ВАСИЛЕВ ВЪРБАНОВ". It is present in stenograms 676, 678, 679, 680, 681, 742.


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
