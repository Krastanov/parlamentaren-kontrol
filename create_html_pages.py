# -*- coding: utf-8 -*-
import os

from mako.lookup import TemplateLookup

import numpy as np

from pk_db import cur, subcur
from pk_logging import logging
from pk_plots import *


##############################################################################
# Copy static files.
##############################################################################
os.system('cp -r raw_components/htmlkickstart/css generated_html/css')
os.system('cp -r raw_components/htmlkickstart/js generated_html/js')
os.system('cp raw_components/style.css generated_html/style.css')
os.system('cp raw_components/286px-Coat_of_arms_of_Bulgaria.svg.wikicommons.png generated_html/logo.png')
os.system('cp raw_components/retina_dust/retina_dust.png generated_html/css/img/grid.png')
os.system('cp raw_components/google93d3e91ac1977e5b.html generated_html/google93d3e91ac1977e5b.html')


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
# Per MP stuff.
##############################################################################
# Load the information.
cur.execute("""SELECT mp_name,
                      orig_party_name,
                      (SELECT LAST(with_party ORDER BY mp_reg.stenogram_date) FROM mp_reg where mp_reg.mp_name = mps.mp_name),
                      (SELECT COUNT(*) FROM mp_reg   where mps.mp_name = mp_reg.mp_name   AND mp_reg.reg = 'present'),
                      (SELECT COUNT(*) FROM mp_reg   where mps.mp_name = mp_reg.mp_name   AND mp_reg.reg = 'absent'),
                      (SELECT COUNT(*) FROM mp_reg   where mps.mp_name = mp_reg.mp_name   AND mp_reg.reg = 'manually_registered'),
                      (SELECT COUNT(*) FROM mp_votes where mps.mp_name = mp_votes.mp_name AND mp_votes.vote = 'yes'),
                      (SELECT COUNT(*) FROM mp_votes where mps.mp_name = mp_votes.mp_name AND mp_votes.vote = 'no'),
                      (SELECT COUNT(*) FROM mp_votes where mps.mp_name = mp_votes.mp_name AND mp_votes.vote = 'abstain'),
                      (SELECT COUNT(*) FROM mp_votes where mps.mp_name = mp_votes.mp_name AND mp_votes.vote = 'absent')
               FROM mps
               ORDER BY mp_name""")
name_orig_with_regs_votes = cur.fetchall()
# Plots

# HTML
logger_html.info("Generating summary html page with MP details.")
per_mp_template = templates.get_template('mps_template.html')
with open('generated_html/mps.html', 'w') as html_file:
    html_file.write(per_mp_template.render(name_orig_with_regs_votes=name_orig_with_regs_votes))


##############################################################################
# Per stenogram stuff.
##############################################################################
# Load templates.
per_stenogram_template = templates.get_template('stenogramN_template.html')
per_stenogram_reg_template = templates.get_template('stenogramNregistration_template.html')
per_stenogram_vote_template = templates.get_template('stenogramNvoteI_template.html')

# Get all stenograms into an iterator.
cur.execute("""SELECT COUNT(*) FROM stenograms""")
len_stenograms = cur.fetchone()[0]
cur.execute("""SELECT stenogram_date, text, vote_line_nb, problem
               FROM stenograms
               ORDER BY stenogram_date""")

for st_i, (stenogram_date, text, vote_line_nb, problem) in enumerate(cur):

    datestr = stenogram_date.strftime('%Y%m%d')
    logger_html.info("Generating HTML and plots for %s - %d of %d" % (datestr, st_i+1, len_stenograms))

    if problem:
        logger_html.error("The database reports problems with stenogram %s. Skipping." % datestr)
        # Generate the main page for the current stenogram.
        with open('generated_html/stenogram%s.html'%datestr, 'w') as html_file:
            html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                          problem=True,
                                                          vote_descriptions=None,
                                                          party_names=None,
                                                          votes_by_session_type_party=None,
                                                          reg_presences=None,
                                                          reg_expected=None,
                                                          text=text,
                                                          vote_line_nb=vote_line_nb))
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


    ################################
    # Registration data per party. #
    ################################

    # Load the registration-by-name data.
    subcur.execute("""SELECT mp_name, with_party, reg
                      FROM mp_reg
                      WHERE stenogram_date = %s
                      ORDER BY mp_name""",
                      (stenogram_date,))
    reg_by_name = subcur.fetchall()

    # Generate registration summary for the current stenogram.
    with open('generated_html/stenogram%sregistration.html'%datestr, 'w') as html_file:
        html_file.write(per_stenogram_reg_template.render(stenogram_date=stenogram_date,
                                                          party_names=party_names,
                                                          reg_presences=reg_presences,
                                                          reg_expected=reg_expected,
                                                          reg_by_name=reg_by_name))


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
        absences_figures(stenogram_date, party_names, votes_absences, votes_absences_percent)

        # Generate plots and html dedicated to a single session.
        for session_i, (description, votes_by_name, (yes, no, abstain, absences))\
            in enumerate(zip(vote_descriptions, votes_by_session_by_name, votes_by_session_type_party)):
            # Plot per-session vote data.
            votes_by_party_figure(stenogram_date, session_i, party_names, yes, no, abstain, absences)
            # Generate per-session html summary.
            with open('generated_html/stenogram%svote%d.html'%(datestr, session_i+1), 'w') as html_file:
                html_file.write(per_stenogram_vote_template.render(stenogram_date=stenogram_date,
                                                                   session_i=session_i,
                                                                   description=description,
                                                                   party_names=party_names,
                                                                   yes=yes, no=no, abstain=abstain,
                                                                   absences=absences,
                                                                   votes_by_name=votes_by_name))

        #######################################################
        # Big summary page in case there are voting sessions. #
        #######################################################
        # Generate the main page for the current stenogram.
        with open('generated_html/stenogram%s.html'%datestr, 'w') as html_file:
            html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                          problem=False,
                                                          vote_descriptions=vote_descriptions,
                                                          party_names=party_names,
                                                          votes_by_session_type_party=votes_by_session_type_party,
                                                          reg_presences=reg_presences,
                                                          reg_expected=reg_expected,
                                                          text=text,
                                                          vote_line_nb=vote_line_nb))

    ##########################################################
    # Big summary page in case there are no voting sessions. #
    ##########################################################
    # Generate the main page for the current stenogram.
    with open('generated_html/stenogram%s.html'%datestr, 'w') as html_file:
        html_file.write(per_stenogram_template.render(stenogram_date=stenogram_date,
                                                      problem=False,
                                                      vote_descriptions=None,
                                                      party_names=party_names,
                                                      votes_by_session_type_party=None,
                                                      reg_presences=reg_presences,
                                                      reg_expected=reg_expected,
                                                      text=text,
                                                      vote_line_nb=vote_line_nb))


##############################################################################
# All stenograms.
##############################################################################
# Get all stenogram dates and session info into a dict.
cur.execute("""SELECT stenogram_date
               FROM stenograms
               ORDER BY stenogram_date""")
stenograms = {}
for (date, ) in cur:
    subcur.execute("""SELECT description
                      FROM vote_sessions
                      WHERE stenogram_date = %s
                      ORDER BY session_number""",
                      (date,))
    stenograms[date] = [v[0] for v in subcur]

# Generate the summary page for all stenograms.
logger_html.info("Generating html summary page of all stenograms.")
all_stenograms_template = templates.get_template('stenograms_template.html')
with open('generated_html/stenograms.html', 'w') as html_file:
    html_file.write(all_stenograms_template.render(stenograms=stenograms))


##############################################################################
# MP emails
##############################################################################
# Get all mails into a dict.
cur.execute("""SELECT party_name
               FROM parties
               ORDER BY party_name""")
mails_per_party_dict = {}
for (party, ) in cur:
    subcur.execute("""SELECT email
                      FROM mps
                      WHERE orig_party_name = %s""",
                      (party,))
    mails = [m[0] for m in subcur]
    if mails:
        mails_per_party_dict[party] = ', '.join([m for m in mails if m])

#Generate the webpage with the mails.
logger_html.info("Generating html page of MP mail addresses.")
mails_template = templates.get_template('mails_template.html')
with open('generated_html/mails.html', 'w') as html_file:
    html_file.write(mails_template.render(mails_per_party_dict=mails_per_party_dict))


##############################################################################
# Static pages
##############################################################################

# Index
logger_html.info("Generating html index page.")
index_template = templates.get_template('index_template.html')
with open('generated_html/index.html', 'w') as html_file:
    html_file.write(index_template.render())

# Contacts
logger_html.info("Generating html contacts page.")
contacts_template = templates.get_template('contacts_template.html')
with open('generated_html/contacts.html', 'w') as html_file:
    html_file.write(contacts_template.render())

