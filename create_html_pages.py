# -*- coding: utf-8 -*-
from mako.template import Template
from mako.lookup import TemplateLookup
from stenograms_to_db import *
from matplotlib import rcParams
import matplotlib.pyplot as plt
import numpy as np
import os
import cPickle

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['FreeSans']
rcParams['figure.figsize'] = (5, 3)
rcParams['figure.dpi'] = 80

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

def registration_figure(datestr, reg_by_party_dict):
    list_of_regs = sorted(reg_by_party_dict.items(), key=lambda x: x[0])
    names = [x[0] for x in list_of_regs]
    presences = np.array([x[1].present for x in list_of_regs])
    expected = np.array([x[1].expected for x in list_of_regs])
    absences = expected - presences

    pos = np.arange(len(names))
    width = 0.35
    plt.clf()
    p1 = plt.bar(pos, presences, width, color='g')
    p2 = plt.bar(pos, absences, width, color='r', bottom=presences)
    plt.ylabel(u'Брой Депутати')
    plt.title(u'Регистрирани Депутати')
    plt.xticks(pos+width/2., names)
    plt.xlim(-0.5*width, pos[-1]+1.5*width)
    plt.legend((p1[0], p2[0]), (u'Присъстващи', u'Отсъстващи'))
    plt.savefig('generated_html/registration%s.png' % datestr)

def votes_by_party_figure(datestr, i, vote_by_party_dict, reg_by_party_dict):
    list_of_votes = sorted(vote_by_party_dict.items(), key=lambda x: x[0])
    names = [x[0] for x in list_of_votes]
    expected = np.array([reg_by_party_dict[n].expected for n in names])
    yes = np.array([x[1].yes for x in list_of_votes])
    no = np.array([x[1].no for x in list_of_votes])
    abstained = np.array([x[1].abstained for x in list_of_votes])
    absences = expected - yes - no - abstained

    pos = np.arange(len(names))
    width = 0.35
    plt.clf()
    p1 = plt.bar(pos, yes, width, color='g')
    p2 = plt.bar(pos, no, width, color='r', bottom=yes)
    p3 = plt.bar(pos, abstained, width, color='c', bottom=yes+no)
    p4 = plt.bar(pos, absences, width, color='k', bottom=yes+no+abstained)
    plt.ylabel(u'Брой Депутати')
    plt.title(u'Гласували Депутати')
    plt.xticks(pos+width/2., names)
    plt.xlim(-0.5*width, pos[-1]+1.5*width)
    plt.legend((p1[0], p2[0], p3[0], p4[0]), (u'За', u'Против', u'Въздържали се', u'Отсъстващи'))
    plt.savefig('generated_html/session%svotes%s.png' % (datestr, i))

per_stenogram_template = templates.get_template('stenogramN_template.html')
for st in stenograms.values():
    datestr = st.date.strftime('%Y%m%d')
    registration_figure(datestr, st.reg_by_party_dict)
    for i, session in enumerate(st.sessions):
        votes_by_party_figure(datestr, i, session.votes_by_party_dict, st.reg_by_party_dict)
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

