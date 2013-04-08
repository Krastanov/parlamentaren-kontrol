# -*- coding: utf-8 -*-
import bisect
import collections
import itertools
import json
import operator
import os

from mako.lookup import TemplateLookup

import numpy as np

from pk_db import db, cur, subcur
from pk_logging import logging
from pk_plots import (registration_figure, absences_figure,
        session_votes_by_party_figure, alltime_regs, alltime_votes,
        alltime_regs_singleMP, alltime_votes_singleMP_compare_all,
        alltime_votes_singleMP_compare_party, evolution_of_votes_singleMP)

from pk_tools import unidecode

def index(a, x):
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError

groupby_list = lambda l, kf: [(k, list(v)) for k, v in itertools.groupby(l, kf)]

##############################################################################
# Load templates.
##############################################################################
templates = TemplateLookup(directories=['mako_templates'],
                           input_encoding='utf-8',
                           output_encoding='utf-8',
                           strict_undefined=True)


##############################################################################
# Prepare loggers.
##############################################################################
logger_html = logging.getLogger('static_html_gen')


##############################################################################
# Set up sitemap.
##############################################################################
class Sitemap(object):
    def __init__(self):
        self.base_string = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n%s\n</urlset>'
        self.url_string = '<url><loc>http://www.parlamentaren-kontrol.com/%s</loc><priority>%0.1f</priority>%s</url>'
        self.image_string = '<image:image><image:loc>http://www.parlamentaren-kontrol.com/%s</image:loc><image:caption>%s</image:caption></image:image>'
        self.content_tuples = []

    def add(self, loc, priority, images=[]):
        self.content_tuples.append((loc, priority, images))

    def write(self):
        logger_html.info("Write down the sitemap.")
        url_strings = (self.url_string % (t[0],
                                          t[1],
                                          '\n '.join(self.image_string % im for im in t[2]))
                       for t in self.content_tuples)
        string = self.base_string % '\n'.join(url_strings)
        with open('generated_html/sitemap.xml', 'w') as sitemap_file:
            sitemap_file.write(string.encode('utf-8'))
        with open('generated_html/robots.txt', 'w') as robots_file:
            robots_file.write('Sitemap: http://www.parlamentaren-kontrol.com/sitemap.xml')

sitemap = Sitemap()


##############################################################################
# Copy static files.
##############################################################################
def copy_static():
    logger_html.info("Copy the static files.")
    os.system('cp -rT raw_components/htmlkickstart/css generated_html/css')
    os.system('cp -rT raw_components/htmlkickstart/js generated_html/js')
    os.system('cp -rT js generated_html/js')
    os.system('cp css/style.css generated_html/style.css')
    os.system('cp raw_components/coat_of_arms.png generated_html/logo.png')
    os.system('cp raw_components/retina_dust/retina_dust.png generated_html/css/img/grid.png')
    os.system('cp raw_components/google93d3e91ac1977e5b.html generated_html/google93d3e91ac1977e5b.html')
    os.system('cp raw_components/BingSiteAuth.xml generated_html/BingSiteAuth.xml')


##############################################################################
# Prepare the SQL dump.
##############################################################################
def write_sql_dump():
    logger_html.info("Prepare the SQL dump.")
    os.system('pg_dump parlamentarenkontrol -U parlamentarenkontrol | gzip > generated_html/parlamentaren_kontrol_SQL_dump.gz')


##############################################################################
# Static pages
##############################################################################
def write_static_pages():
    # Index
    logger_html.info("Generating html index page.")
    index_template = templates.get_template('index_template.html')
    with open('generated_html/index.html', 'w') as html_file:
        html_file.write(index_template.render())
        sitemap.add('', 0.5)

    # Contacts
    logger_html.info("Generating html contacts page.")
    contacts_template = templates.get_template('contacts_template.html')
    with open('generated_html/contacts.html', 'w') as html_file:
        html_file.write(contacts_template.render())
        sitemap.add('contacts.html', 0.4)


##############################################################################
# MP emails
##############################################################################
def write_MPs_emails_page():
    logger_html.info("Generating list page for MP emails.")
    # Get all mails into a dict.
    mailscur = db.cursor()
    mailscur.execute("""SELECT email, orig_party_name FROM mps ORDER BY orig_party_name""")
    groups = itertools.groupby(mailscur, operator.itemgetter(1))
    mails_by_party_dict = {k: ', '.join(m[0] for m in mails if m[0]) for k, mails in groups}

    #Generate the webpage with the mails.
    logger_html.info("Generating html page of MP mail addresses.")
    mails_template = templates.get_template('mails_template.html')
    with open('generated_html/mails.html', 'w') as html_file:
        html_file.write(mails_template.render(mails_by_party_dict=mails_by_party_dict))
        sitemap.add('mails.html', 0.8)


##############################################################################
# Graph visualizations.
##############################################################################
def write_graph_visualizations():
    logger_html.info("Generating the graph visualizations.")
    # Load the information.
    cur.execute("""SELECT mp_name, orig_party_name
                   FROM mps
                   WHERE (SELECT COUNT(*) FROM mp_reg WHERE mps.mp_name = mp_reg.mp_name) > 150""")
    name_party_dict = dict(cur.fetchall())
    parties = sorted(list(set(name_party_dict.values())))
    name = sorted(name_party_dict.keys())
    n_index_dict = dict(zip(name, range(len(name))))

    cur.execute("""SELECT stenogram_date, session_number
                   FROM vote_sessions
                   ORDER BY stenogram_date, session_number""")
    date_session = cur.fetchall()
    ds_index_dict = dict(zip(date_session, range(len(date_session))))

    # yes=1 no=-1 abst/absent=0
    is_yes_no_abst_absent  = np.zeros((len(name), len(date_session)), np.float16)
    named_cur = db.cursor(name="sever_side_due_to_low_memory")
    named_cur.execute("""SELECT mp_name, stenogram_date, session_number, vote
                   FROM mp_votes""")
    for n, d, s, v in named_cur:
        i_n = n_index_dict.get(n)
        if i_n is None:
            continue
        i_ds = ds_index_dict[(d, s)]
        is_yes_no_abst_absent[i_n, i_ds] = {'yes':1, 'no':-1, 'abstain':0, 'absent':0}[v]
    named_cur.close()

    # Prepare the graph matrix.
    abses = np.sum(is_yes_no_abst_absent==0)
    tots = is_yes_no_abst_absent.size
    not_abses = tots - abses
    M_diff = np.tensordot(is_yes_no_abst_absent, is_yes_no_abst_absent, axes=([1],[1]))
    M_tot  = np.tensordot(abs(is_yes_no_abst_absent), abs(is_yes_no_abst_absent), axes=([1],[1]))
    del is_yes_no_abst_absent
    M = M_diff/(M_tot+0.00001)
    C = np.median(M_tot)
    M[M_tot<C] = 0
    M[M<0.5] = 0
    M = M*2-1
    del M_diff, M_tot
    M, temp = np.zeros_like(M), M
    indices = np.argmax(temp, axis=1)
    M[indices,:] = temp[indices,:]
    M = M + M.T
    del temp


    # Make the JSON dumps.
    json_dict = {}
    json_dict['nodes'] = [{'name':'%s - %s'%(n, name_party_dict[n]),
                           'group':parties.index(name_party_dict[n]),
                           'datalegend':name_party_dict[n]}
                          for n in name]
    json_dict['links'] = [{'source':j, 'target':i, 'value':float(M[i,j])}
                          for j in range(len(name))
                          for i in range(j)
                          if M[i,j]>0]
    with open('generated_html/graph_all.json','w') as f:
        f.write(json.dumps(json_dict))
    for p in parties:
        asciiname = unidecode(p)
        json_dict = {}
        restricted_name = [n for n in name if name_party_dict[n]==p]
        json_dict['nodes'] = [{'name':n, 'group':0, 'datalegend':p}
                              for n in restricted_name]
        json_dict['links'] = [{'source':j, 'target':i, 'value':float(M[n_index_dict[restricted_name[i]],n_index_dict[restricted_name[j]]])}
                              for j in range(len(restricted_name))
                              for i in range(j)
                              if M[n_index_dict[restricted_name[i]],n_index_dict[restricted_name[j]]]>0 and name_party_dict[n]==p]
        with open('generated_html/graph_%s.json'%asciiname,'w') as f:
            f.write(json.dumps(json_dict))

    # HTML
    graph_template = templates.get_template('forcegraph_template.html')
    bg_en_party_names = zip(parties, map(unidecode, parties)) + [(u'всички партии', 'all')]
    for bg_name, en_name in bg_en_party_names:
        filename = 'forcegraph_%s.html'%en_name
        with open('generated_html/%s'%filename, 'w') as html_file:
            html_file.write(graph_template.render(bg_name=bg_name, en_name=en_name, bg_en_party_names=bg_en_party_names))
            sitemap.add(filename, 0.8)


##############################################################################
# Per MP stuff.
##############################################################################
#TODO probably rewrite in pandas panel objects (and deal with NaNs)
def write_MPs_overview_page():
    logger_html.info("Generating summary html page with MP details.")

    #########################
    # Load the information. #
    #########################

    # All MPs
    mpscur = db.cursor()
    mpscur.execute("""SELECT mp_name,
                             orig_party_name,
                             (SELECT LAST(with_party ORDER BY mp_reg.stenogram_date) FROM mp_reg WHERE mp_reg.mp_name = mps.mp_name),
                             original_url
                      FROM mps
                      ORDER BY orig_party_name, mp_name""")
    mps = mpscur.fetchall()
    parties = groupby_list(mps, operator.itemgetter(1))

    # All sessions
    sescur = db.cursor()
    sescur.execute("""SELECT stenogram_date, session_number
                      FROM vote_sessions
                      ORDER BY stenogram_date, session_number""")
    sessions = sescur.fetchall()
    session_dates = groupby_list(sessions, operator.itemgetter(0))

    # All dates - includes dates on which no voting was done
    datecur = db.cursor()
    datecur.execute("""SELECT stenogram_date
                       FROM stenograms
                       ORDER BY stenogram_date""")
    all_dates = [d[0] for d in datecur]

    def aggregate_sessions_in_dates(array):
        new_shape = list(array.shape)
        new_shape[1] = len(session_dates)
        new_array = np.zeros(new_shape, dtype=np.int32)
        i = 0
        for date_i, date in enumerate(session_dates):
            end = i+len(date[1])
            new_array[:,date_i,:] = np.sum(array[:,i:end,:], 1)
            i = end
        return new_array

    def aggregate_names_in_parties(array):
        new_shape = list(array.shape)
        new_shape[0] = len(parties)
        new_array = np.zeros(new_shape, dtype=np.int32)
        i = 0
        for party_i, party in enumerate(parties):
            end = i+len(party[1])
            new_array[party_i,:,:] = np.sum(array[i:end,:,:], 0)
            i = end
        return new_array

    # All regs.
    datacur = db.cursor()
    mps_dates_reg = np.zeros((len(mps), len(all_dates), 3), dtype=np.int32)
    """ A 3D array with the same structure as above."""
    reg_dict = {'present':0, 'absent':1, 'manually_registered':2}
    for (mp_i, mp) in enumerate(mps):
        datacur.execute("""SELECT reg, stenogram_date FROM mp_reg
                           WHERE mp_name = %s
                           ORDER BY stenogram_date""",
                           (mp[0],))
        f =  datacur.fetchone()
        for r in datacur:
            date_i = index(all_dates, r[1])
            mps_dates_reg[mp_i, date_i, reg_dict[r[0]]] = 1

    mps_all_reg = np.sum(mps_dates_reg, 1)

    # All votes
    mps_sessions_vote = np.zeros((len(mps), len(sessions), 4), dtype=np.int32)
    """  A 3D array       sessions /
         with the         index   /___yes_no_abst_absent
         following               |    0   0   0   1
         structure:        names |    1   0   0   0
                           index |   ...
         Contains votes. If the MP was not even registered for the session it contains only zeros."""
    vote_dict = {'yes':0, 'no':1, 'abstain':2, 'absent':3}
    for (mp_i, mp) in enumerate(mps):
        datacur.execute("""SELECT vote, stenogram_date, session_number FROM mp_votes
                           WHERE mp_name = %s
                           ORDER BY stenogram_date, session_number""",
                           (mp[0],))
        for v in datacur.fetchall():
            ses_i = index(sessions, v[1:])
            mps_sessions_vote[mp_i, ses_i, vote_dict[v[0]]] = 1

    mps_dates_vote = aggregate_sessions_in_dates(mps_sessions_vote)
    parties_sessions_vote = aggregate_names_in_parties(mps_sessions_vote)
    parties_dates_vote = aggregate_sessions_in_dates(parties_sessions_vote)
    mps_all_vote = np.sum(mps_dates_vote, 1)
    all_sessions_vote = np.sum(parties_sessions_vote, 0)
    """3D and 2D arrays with aggregated data."""

    mps_sessions_with_against_party = np.zeros((len(mps), len(sessions), 2), dtype=np.int32)
    """ A 3D array with the same structure as above. The data is vote with/against party."""
    offset = 0
    for p_i, (party, p_mps) in enumerate(parties):
        end = offset + len(p_mps)
        for mp_i, ses_i in itertools.product(range(offset, end), range(len(sessions))):
            if not any(mps_sessions_vote[mp_i, ses_i, :2]):
                continue
            if parties_sessions_vote[p_i, ses_i, 0] == parties_sessions_vote[p_i, ses_i, 1]:
                mps_sessions_with_against_party[mp_i, ses_i, 0] = 1
                continue
            mps_sessions_with_against_party[mp_i, ses_i, 0] = mps_sessions_vote[mp_i, ses_i, np.argmax(parties_sessions_vote[p_i, ses_i, :2])]
            mps_sessions_with_against_party[mp_i, ses_i, 1] = 1 - mps_sessions_with_against_party[mp_i, ses_i, 0]
        offset = end

    mps_dates_with_against_party = aggregate_sessions_in_dates(mps_sessions_with_against_party)
    mps_all_with_against_party = np.sum(mps_dates_with_against_party, 1)
    """3D and 2D arrays with aggregated data."""

    mps_sessions_with_against_all = np.zeros((len(mps), len(sessions), 2), dtype=np.int32)
    """ A 3D array with the same structure as above. The data is vote with/against all."""
    for mp_i, ses_i in itertools.product(range(len(mps)), range(len(sessions))):
        if not any(mps_sessions_vote[mp_i, ses_i, :2]):
            continue
        if all_sessions_vote[ses_i, 0] == all_sessions_vote[ses_i, 1]:
            mps_sessions_with_against_all[mp_i, ses_i, 0] = 1
            continue
        mps_sessions_with_against_all[mp_i, ses_i, 0] = mps_sessions_vote[mp_i, ses_i, np.argmax(all_sessions_vote[ses_i, :2])]
        mps_sessions_with_against_all[mp_i, ses_i, 1] = 1 - mps_sessions_with_against_all[mp_i, ses_i, 0]

    mps_dates_with_against_all = aggregate_sessions_in_dates(mps_sessions_with_against_all)
    mps_all_with_against_all = np.sum(mps_dates_with_against_all, 1)
    """3D and 2D arrays with aggregated data."""

    ############
    # Summary. #
    ############

    # Plots
    alltime_regs(*np.sum(mps_all_reg, 0))
    alltime_votes(*np.sum(all_sessions_vote, 0))

    # HTML
    mps_template = templates.get_template('mps_template.html')
    with open('generated_html/mps.html', 'w') as html_file:
        html_file.write(mps_template.render(mps=mps,
                                            mps_all_reg=mps_all_reg,
                                            mps_all_vote=mps_all_vote,
                                            mps_all_with_against_party=mps_all_with_against_party,
                                            mps_all_with_against_all=mps_all_with_against_all))
        sitemap.add('mps.html', 0.8, [('alltimeregs.png', u'Oтсъствия на депутати по време на регистрация.'),
                                      ('alltimevotes.png', u'Гласове и отсъствия на депутати по време на гласувания.')])

    #################
    # Per MP pages. #
    #################

    per_mp_template = templates.get_template('mp_N_template.html')
    only_dates = [d[0] for d in session_dates]
    for mp_i, (name, party, party_now, original_url) in enumerate(mps):
        asciiname = unidecode(name).replace(' ', '_').lower()
        alltime_regs_singleMP(mps_all_reg[mp_i,:], name, asciiname)
        alltime_votes_singleMP_compare_all(mps_all_with_against_all[mp_i,:],
                                           mps_all_vote[mp_i,2:],
                                           name, asciiname)
        alltime_votes_singleMP_compare_party(mps_all_with_against_party[mp_i,:],
                                             mps_all_vote[mp_i,2:],
                                             name, asciiname)
        evolution_of_votes_singleMP(only_dates,
                                    mps_dates_vote[mp_i,:,:],
                                    mps_dates_with_against_all[mp_i,:,:],
                                    mps_dates_with_against_party[mp_i,:,:],
                                    name, asciiname)
        with open('generated_html/mp_%s.html'%asciiname, 'w') as html_file:
            html_file.write(per_mp_template.render(name=name,
                                                   asciiname=asciiname,
                                                   party=party,
                                                   party_now=party_now,
                                                   vote=mps_all_vote[mp_i,:],
                                                   with_against_p=mps_all_with_against_party[mp_i,:],
                                                   with_against_a=mps_all_with_against_all[mp_i,:],
                                                   reg=mps_all_reg[mp_i,:],
                                                   original_url=original_url))
            sitemap.add('mp_%s.html'%asciiname, 0.7,
                        [('vote_evol_%s.png'%asciiname, u'Гласовете и отсъствията на %s през годините.'%name),
                         ('alltimeregs_%s.png'%asciiname, u'Oтсъствия на %s по време на регистрация.'%name),
                         ('alltimevotes_compare_all_%s.png'%asciiname, u'Гласове и отсъствия на %s по време на гласувания (сравнение с мнозинството).'%name),
                         ('alltimevotes_compare_party_%s.png'%asciiname, u'Гласове и отсъствия на %s по време на гласувания (сравнение с позицията на партията).'%name)])



##############################################################################
# List of stenograms summary pages.
##############################################################################
def write_list_of_stenograms_summary_pages():
    logger_html.info("Generating html summary page of all stenograms.")
    all_stenograms_template = templates.get_template('stenograms_template.html')

    sessionscur = db.cursor()
    sessionscur.execute("""SELECT description, stenogram_date
                           FROM vote_sessions
                           ORDER BY stenogram_date, session_number""")
    date_stenogr = groupby_list(sessionscur, operator.itemgetter(1))

    year_date_stenogr = groupby_list(date_stenogr, lambda d_s: d_s[0].year)
    years = zip(*year_date_stenogr)[0]
    for y, y_date_stenogr in year_date_stenogr:
        month_date_stenogr = [('all', y_date_stenogr)] + groupby_list(y_date_stenogr, lambda d_s: d_s[0].month)
        months = zip(*month_date_stenogr)[0]
        for m, m_date_stenogr in month_date_stenogr:
            with open('generated_html/stenograms%s%s.html'%(y,m), 'w') as html_file:
                html_file.write(all_stenograms_template.render(years=years,
                                                               months=months,
                                                               current_y=y,
                                                               stenogram_mgroup=m_date_stenogr))
                sitemap.add('stenograms%s%s.html'%(y,m), 0.8)

    # Copy the most recent one
    os.system('cp generated_html/stenograms%s%s.html generated_html/stenograms.html'%(y,m))
    sitemap.add('stenograms.html', 0.8)


##############################################################################
# Per stenogram stuff.
##############################################################################
def write_stenogram_pages():
    # Load templates.
    per_stenogram_template = templates.get_template('stenogramN_template.html')
    per_stenogram_reg_template = templates.get_template('stenogramNregistration_template.html')
    per_stenogram_vote_template = templates.get_template('stenogramNvoteI_template.html')

    # Get all stenograms into an iterator.
    cur.execute("""SELECT COUNT(*) FROM stenograms""")
    len_stenograms = cur.fetchone()[0]
    cur.execute("""SELECT stenogram_date, text, vote_line_nb, problem, original_url
                   FROM stenograms
                   ORDER BY stenogram_date""")

    for st_i, (stenogram_date, text, vote_line_nb, problem, original_url) in enumerate(cur):

        datestr = stenogram_date.strftime('%Y%m%d')
        logger_html.info("Generating HTML and plots for %s - %d of %d" % (datestr, st_i+1, len_stenograms))

        if problem:
            logger_html.error("The database reports problems with stenogram %s. Skipping." % datestr)
            # Generate the main page for the current stenogram.
            filename = 'stenogram%s.html'%datestr
            with open('generated_html/%s'%filename, 'w') as html_file:
                html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                              problem=True,
                                                              original_url=original_url,
                                                              vote_descriptions=None,
                                                              party_names=None,
                                                              votes_by_session_type_party=None,
                                                              reg_presences=None,
                                                              reg_expected=None,
                                                              text=text,
                                                              vote_line_nb=vote_line_nb))
                sitemap.add(filename, 0.7)
            continue

        ################################
        # Registration data per party. #
        ################################

        # Load all party registration data for the current stenogram.
        subcur.execute("""SELECT party_name, present, expected
                          FROM party_reg
                          WHERE stenogram_date = %s
                          ORDER BY party_name""",
                          (stenogram_date,))
        party_names, reg_presences, reg_expected = zip(*subcur.fetchall())
        party_names = [n for n in party_names]
        reg_presences = np.array(reg_presences)
        reg_expected = np.array(reg_expected)

        # Plot registration data.
        registration_figure(stenogram_date, party_names, reg_presences, reg_expected)

        # Load the registration-by-name data.
        subcur.execute("""SELECT mp_name, with_party, reg
                          FROM mp_reg
                          WHERE stenogram_date = %s
                          ORDER BY mp_name""",
                          (stenogram_date,))
        reg_by_name = subcur.fetchall()

        # Generate registration summary for the current stenogram.
        filename = 'stenogram%sregistration.html'%datestr
        with open('generated_html/%s'%filename, 'w') as html_file:
            html_file.write(per_stenogram_reg_template.render(stenogram_date=stenogram_date,
                                                              party_names=party_names,
                                                              reg_presences=reg_presences,
                                                              reg_expected=reg_expected,
                                                              reg_by_name=reg_by_name))
            sitemap.add(filename, 0.6, [('registration%s.png' % stenogram_date.strftime('%Y%m%d'),
                                         u'Регистрирани и отсъстващи депутати на %s.' % stenogram_date.strftime('%Y-%m-%d'))])


        #########################
        # Voting sessions data. #
        #########################

        # Check whether there were any voting sessions at all.
        subcur.execute("""SELECT COUNT(*) FROM vote_sessions WHERE stenogram_date = %s""", (stenogram_date,))
        len_sessions = subcur.fetchone()[0]

        if len_sessions:

            ###########
            # LOADING #
            ###########

            # Load all party absence and vote data for all sessions of the current stenogram.
            # list format: vote_* is [party1_votes, ...], party*_votes is [session1_vote, ...], session*_vote is int
            votes_yes = []
            votes_no = []
            votes_abstain = []
            votes_total = []
            votes_absences = []
            votes_absences_percent = []
            for party_i, n in enumerate(party_names):
                subcur.execute("""SELECT yes, no, abstain, total
                                  FROM party_votes
                                  WHERE stenogram_date = %s
                                  AND party_name = %s
                                  ORDER BY session_number""",
                                  (stenogram_date, n))
                yes, no, abstain, total = map(np.array, zip(*subcur))
                votes_yes.append(yes)
                votes_no.append(no)
                votes_abstain.append(abstain)
                votes_total.append(total)
                absent_party = reg_expected[party_i] - total
                votes_absences.append(absent_party)
                votes_absences_percent.append(absent_party*100/reg_expected[party_i])
            votes_by_session_type_party = np.array([votes_yes, votes_no, votes_abstain, votes_absences
                                                   ]).transpose(2,0,1)

            # Load all session descriptions for the current stenogram.
            subcur.execute("""SELECT description
                              FROM vote_sessions
                              WHERE stenogram_date = %s
                              ORDER BY session_number""",
                              (stenogram_date,))
            vote_descriptions = [d[0] for d in subcur]

            # Load the list-by-mp-name vote for each session.
            votes_by_session_by_name = []
            for session_i in range(len_sessions):
                subcur.execute("""SELECT mp_name, with_party, vote
                                  FROM mp_votes
                                  WHERE session_number = %s
                                  AND stenogram_date = %s
                                  ORDER BY mp_name""",
                                  (session_i, stenogram_date))
                votes_by_session_by_name.append(subcur.fetchall())

            ##############
            # PRESENTING #
            ##############

            # Plot absences timeseries.
            absences_figure(stenogram_date, party_names, votes_absences, votes_absences_percent)

            # Generate plots and html dedicated to a single session.
            for session_i, (description, votes_by_name, votes_by_type_party)\
                in enumerate(zip(vote_descriptions, votes_by_session_by_name, votes_by_session_type_party)):
                # Plot per-session vote data.
                session_votes_by_party_figure(stenogram_date, session_i, party_names, *votes_by_type_party)
                # Generate per-session html summary.
                filename = 'stenogram%svote%d.html'%(datestr, session_i+1)
                with open('generated_html/%s'%filename, 'w') as html_file:
                    html_file.write(per_stenogram_vote_template.render(stenogram_date=stenogram_date,
                                                                       session_i=session_i,
                                                                       description=description,
                                                                       party_names=party_names,
                                                                       votes_by_type_party=votes_by_type_party,
                                                                       votes_by_name=votes_by_name))
                    sitemap.add(filename, 0.6, [('session%svotes%s.png' % (stenogram_date.strftime('%Y%m%d'), session_i+1),
                                                 u'Разпределение на гласовете и отсътвията на депутати по партии на %s за гласуване номер %s.' % (stenogram_date.strftime('%Y-%m-%d'), session_i+1))])

            #######################################################
            # Big summary page in case there are voting sessions. #
            #######################################################
            # Generate the main page for the current stenogram.
            filename = 'stenogram%s.html'%datestr
            with open('generated_html/%s'%filename, 'w') as html_file:
                html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                              problem=False,
                                                              original_url=original_url,
                                                              vote_descriptions=vote_descriptions,
                                                              party_names=party_names,
                                                              votes_by_session_type_party=votes_by_session_type_party,
                                                              reg_presences=reg_presences,
                                                              reg_expected=reg_expected,
                                                              text=text,
                                                              vote_line_nb=vote_line_nb))
                sitemap.add(filename, 0.7, [('absences%s.png' % stenogram_date.strftime('%Y%m%d'),
                                             u'Промяна на броя присъстващи/отсъстващи депутати на %s.' % stenogram_date.strftime('%Y-%m-%d'))])
        else:
            ##########################################################
            # Big summary page in case there are no voting sessions. #
            ##########################################################
            # Generate the main page for the current stenogram.
            filename = 'stenogram%s.html'%datestr
            with open('generated_html/%s'%filename, 'w') as html_file:
                html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                              problem=False,
                                                              original_url=original_url,
                                                              vote_descriptions=None,
                                                              party_names=party_names,
                                                              votes_by_session_type_party=None,
                                                              reg_presences=reg_presences,
                                                              reg_expected=reg_expected,
                                                              text=text,
                                                              vote_line_nb=vote_line_nb))
                sitemap.add(filename, 0.7)


##############################################################################
# Execute all.
##############################################################################
todo = [
        copy_static,
        write_sql_dump,
        write_static_pages,
        write_MPs_emails_page,
#        write_graph_visualizations,
        write_MPs_overview_page,
        write_list_of_stenograms_summary_pages,
        write_stenogram_pages,
        sitemap.write
        ]
for f in todo:
    try:
        f()
    except KeyboardInterrupt:
        logger_html.error("Interrupted at %s" % f.__name__)
