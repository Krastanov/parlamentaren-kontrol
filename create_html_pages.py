# -*- coding: utf-8 -*-
from mako.template import Template
from mako.lookup import TemplateLookup
from stenograms_to_db import *
from matplotlib import rcParams, gridspec
import matplotlib.pyplot as plt
import numpy as np
import os
import cPickle

import logging
logging.basicConfig(filename="create_html_pages.log", level=logging.INFO)

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['FreeSans']
rcParams['font.size'] = 10
rcParams['figure.figsize'] = (5., 3)
rcParams['savefig.dpi'] = 90
rcParams['legend.fontsize'] = 'small'
rcParams['text.antialiased'] = True
rcParams['patch.antialiased'] = True
rcParams['lines.antialiased'] = True

os.system('cp -r htmlkickstart/css generated_html/css')
os.system('cp -r htmlkickstart/js generated_html/js')
os.system('cp style.css generated_html/style.css')
os.system('cp retina_dust/retina_dust.png generated_html/css/img/grid.png')
os.system('cp google93d3e91ac1977e5b.html generated_html/google93d3e91ac1977e5b.html')

stenograms_dump = open('data/stenograms_dump', 'r')
stenograms = cPickle.load(stenograms_dump)
stenograms_dump.close()

templates = TemplateLookup(directories=['mako_templates'],
                           input_encoding='utf-8',
                           output_encoding='utf-8')

##############################################################################
# Per stenogram stuff
##############################################################################

def registration_figure(date, reg_by_party_dict):
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    list_of_regs = sorted(reg_by_party_dict.items(), key=lambda x: x[0])
    names = [x[0] for x in list_of_regs]
    presences = np.array([x[1].present for x in list_of_regs])
    expected = np.array([x[1].expected for x in list_of_regs])
    absences = expected - presences

    pos = np.arange(len(names))
    width = 0.35
    f = plt.figure()
    f.suptitle(u'Регистрирани Депутати %s'%datestr_human)
    gs = gridspec.GridSpec(3,5)
    main = f.add_subplot(gs[:,0:-1])
    p1 = main.bar(pos, presences, width, color='g')
    p2 = main.bar(pos, absences, width, color='r', bottom=presences)
    main.set_ylabel(u'Брой Депутати')
    main.set_xticks(pos+width/2.)
    main.set_xticklabels(names)
    main.tick_params(axis='x', length=0)
    main.set_xlim(-0.5*width, pos[-1]+1.5*width)
    main.legend((p1[0], p2[0]), (u'Присъстващи', u'Отсъстващи'), loc='upper left', bbox_to_anchor=(1,1))
    summ = f.add_subplot(gs[-1,-1])
    pie_array = [np.sum(presences), np.sum(absences)]
    summ.pie(pie_array, colors=['g', 'r'])
    summ.set_title(u'Общо')
    f.savefig('generated_html/registration%s.png' % datestr)
    plt.close()

def votes_by_party_figure(date, i, vote_by_party_dict, reg_by_party_dict):
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    list_of_votes = sorted(vote_by_party_dict.items(), key=lambda x: x[0])
    names = [x[0] for x in list_of_votes]
    expected = np.array([reg_by_party_dict[n].expected for n in names])
    yes = np.array([x[1].yes for x in list_of_votes])
    no = np.array([x[1].no for x in list_of_votes])
    abstained = np.array([x[1].abstained for x in list_of_votes])
    absences = expected - yes - no - abstained

    pos = np.arange(len(names))
    width = 0.35
    f = plt.figure()
    f.suptitle(u'Гласували Депутати %s гл.%d' % (datestr_human, i+1))
    gs = gridspec.GridSpec(3,5)
    main = f.add_subplot(gs[:,0:-1])
    p1 = main.bar(pos, yes, width, color='g')
    p2 = main.bar(pos, no, width, color='r', bottom=yes)
    p3 = main.bar(pos, abstained, width, color='c', bottom=yes+no)
    p4 = main.bar(pos, absences, width, color='k', bottom=yes+no+abstained)
    main.set_ylabel(u'Брой Депутати')
    main.set_xticks(pos+width/2.)
    main.set_xticklabels(names)
    main.tick_params(axis='x', length=0)
    main.set_xlim(-0.5*width, pos[-1]+1.5*width)
    main.legend((p1[0], p2[0], p3[0], p4[0]), (u'За', u'Против', u'Въздържали се', u'Отсъстващи'), loc='upper left', bbox_to_anchor=(1,1))
    summ = f.add_subplot(gs[-1,-1])
    pie_array = [np.sum(yes), np.sum(no), np.sum(abstained), np.sum(absences)]
    summ.pie(pie_array, colors=['g', 'r', 'c', 'k'])
    summ.set_title(u'Общо')
    f.savefig('generated_html/session%svotes%s.png' % (datestr, i+1))
    plt.close()

def absences_figures(date, reg_by_party_dict, sessions):
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    list_of_regs = sorted(reg_by_party_dict.items(), key=lambda x: x[0])
    names = [x[0] for x in list_of_regs]
    presences = np.array([x[1].present for x in list_of_regs])
    expected = np.array([x[1].expected for x in list_of_regs])
    reg_absences = expected - presences
    all_absences = [reg_absences]
    for vote_by_party_dict in [s.votes_by_party_dict for s in sessions]:
        yes = np.array([vote_by_party_dict[n].yes for n in names])
        no = np.array([vote_by_party_dict[n].no for n in names])
        abstained = np.array([vote_by_party_dict[n].abstained for n in names])
        all_absences.append(expected - yes - no - abstained)
    all_absences_percent = [a*100/expected for a in all_absences]
    all_absences = np.column_stack(all_absences).T
    all_absences_percent = np.column_stack(all_absences_percent).T

    f = plt.figure()
    f.suptitle(u'Отсъствия по Време на Гласуване %s'%datestr_human)
    gs = gridspec.GridSpec(2,5)
    su = f.add_subplot(gs[0,:-1])
    su.plot(all_absences, alpha=0.8)
    su.set_ylabel(u'Брой Депутати')
    su.set_ylim(0)
    su.set_xticks([])
    su.legend(names, loc='upper left', bbox_to_anchor=(1,1))
    sd = f.add_subplot(gs[1,:-1], sharex=su)
    sd.plot(all_absences_percent, alpha=0.8)
    sd.set_ylabel(u'% от Партията')
    sd.set_xlabel(u'хронологичен ред на гласуванията')
    sd.set_ylim(0, 100)
    sd.set_xticks([])
    sd.set_yticks([25, 50, 75])
    f.autofmt_xdate()
    f.savefig('generated_html/absences%s.png' % datestr)
    plt.close()

per_stenogram_template = templates.get_template('stenogramN_template.html')
for st in stenograms.values():
    datestr = st.date.strftime('%Y%m%d')
    logging.info("At date %s." % datestr)
    registration_figure(st.date, st.reg_by_party_dict)
    absences_figures(st.date, st.reg_by_party_dict, st.sessions)
    for i, session in enumerate(st.sessions):
        votes_by_party_figure(st.date, i, session.votes_by_party_dict, st.reg_by_party_dict)
    with open('generated_html/stenogram%s.html'%datestr, 'w') as html_file:
        html_file.write(per_stenogram_template.render(stenogram=st))


##############################################################################
# All stenograms
##############################################################################

all_stenograms_template = templates.get_template('stenograms_template.html')
with open('generated_html/stenograms.html', 'w') as html_file:
    html_file.write(all_stenograms_template.render(stenograms=stenograms))


##############################################################################
# MP emails
##############################################################################

mails_per_party_dict = {}
for f in ['data/mail_dump%d'%i for i in range(6)]:
    lines = open(f).readlines()
    mails_per_party_dict[lines[0].decode('UTF-8')] = lines[1].decode('UTF-8')

mails_template = templates.get_template('mails_template.html')
with open('generated_html/mails.html', 'w') as html_file:
    html_file.write(mails_template.render(mails_per_party_dict=mails_per_party_dict))


##############################################################################
# Static pages
##############################################################################

# Index
index_template = templates.get_template('index_template.html')
with open('generated_html/index.html', 'w') as html_file:
    html_file.write(index_template.render())

# Contacts
contacts_template = templates.get_template('contacts_template.html')
with open('generated_html/contacts.html', 'w') as html_file:
    html_file.write(contacts_template.render())

