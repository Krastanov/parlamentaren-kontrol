# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, gridspec


##############################################################################
# Matplotlib configuration.
##############################################################################
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['FreeSans']
rcParams['font.size'] = 10
rcParams['figure.figsize'] = (5, 3)
figsize_square = (5, 5)
rcParams['savefig.dpi'] = 90
rcParams['legend.fontsize'] = 'small'
rcParams['text.antialiased'] = True
rcParams['patch.antialiased'] = True
rcParams['lines.antialiased'] = True


##############################################################################
# Per stenogram plots.
##############################################################################
def registration_figure(date, names, reg_presences, reg_expected):
    """Barchart: x:name vs y:stacked presences and absences."""
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    absences = reg_expected - reg_presences

    pos = np.arange(len(names))
    width = 0.35
    f = plt.figure()
    f.suptitle(u'Регистрирани Депутати %s'%datestr_human)
    gs = gridspec.GridSpec(3,5)
    main = f.add_subplot(gs[:,0:-1])
    p1 = main.bar(pos, reg_presences, width, color='g')
    p2 = main.bar(pos, absences, width, color='r', bottom=reg_presences)
    main.set_ylabel(u'Брой Депутати')
    main.set_xticks(pos+width/2.)
    main.set_xticklabels(names)
    main.tick_params(axis='x', length=0)
    main.set_xlim(-0.5*width, pos[-1]+1.5*width)
    main.legend((p1[0], p2[0]), (u'Присъстващи', u'Отсъстващи'), loc='upper left', bbox_to_anchor=(1,1))
    summ = f.add_subplot(gs[-1,-1])
    pie_array = [np.sum(reg_presences), np.sum(absences)]
    summ.pie(pie_array, colors=['g', 'r'])
    summ.set_title(u'Общо')
    f.savefig('generated_html/registration%s.png' % datestr)
    plt.close()

def absences_figure(date, names, vote_absences, vote_absences_percent):
    """Time series chart: x:session nb vs y:absences, color:name"""
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    vote_absences = np.column_stack(vote_absences)
    vote_absences_percent = np.column_stack(vote_absences_percent)

    f = plt.figure()
    f.suptitle(u'Отсъствия по Време на Гласуване %s'%datestr_human)
    gs = gridspec.GridSpec(2,5)
    su = f.add_subplot(gs[0,:-1])
    su.plot(vote_absences, alpha=0.8)
    su.set_ylabel(u'Брой Депутати')
    su.set_ylim(0)
    su.set_xticks([])
    su.legend(names, loc='upper left', bbox_to_anchor=(1,1))
    sd = f.add_subplot(gs[1,:-1], sharex=su)
    sd.plot(vote_absences_percent, alpha=0.8)
    sd.set_ylabel(u'% от Партията')
    sd.set_xlabel(u'хронологичен ред на гласуванията')
    sd.set_ylim(0, 100)
    sd.set_xticks([])
    sd.set_yticks([25, 50, 75])
    f.autofmt_xdate()
    f.savefig('generated_html/absences%s.png' % datestr)
    plt.close()


##############################################################################
# Per stenogram session plots.
##############################################################################
f = plt.figure()                      # XXX "ugly tweak"
gs = gridspec.GridSpec(3,5)           # These were made global and reused,
main = f.add_subplot(gs[:,0:-1])      # giving 2x speedup. The `remove` calls
summ = f.add_subplot(gs[-1,-1])       # below are part of the same tweak.
title = f.suptitle('')
main.set_ylabel(u'Брой Депутати')
summ.set_title(u'Общо')

def session_votes_by_party_figure(date, i, party_names, yes, no, abstain, absences):
    datestr = date.strftime('%Y%m%d')
    datestr_human = date.strftime('%d/%m/%Y')
    pos = np.arange(len(party_names))
    width = 0.35

    global f, main, summ, title

    title.set_text(u'Гласували Депутати %s гл.%d' % (datestr_human, i+1))
    p1 = main.bar(pos, yes, width, color='g')
    p2 = main.bar(pos, no, width, color='r', bottom=yes)
    p3 = main.bar(pos, abstain, width, color='c', bottom=yes+no)
    p4 = main.bar(pos, absences, width, color='k', bottom=yes+no+abstain)
    main.set_xticks(pos+width/2.)
    main.set_xticklabels(party_names)
    main.tick_params(axis='x', length=0)
    main.set_xlim(-0.5*width, pos[-1]+1.5*width)
    main.legend((p1[0], p2[0], p3[0], p4[0]), (u'За', u'Против', u'Въздържали се', u'Отсъстващи'), loc='upper left', bbox_to_anchor=(1,1))
    pie_array = [np.sum(yes), np.sum(no), np.sum(abstain), np.sum(absences)]
    wedges, texts = summ.pie(pie_array, colors=['g', 'r', 'c', 'k'])
    f.savefig('generated_html/session%svotes%s.png' % (datestr, i+1))

    for o in [p1, p2, p3, p4] + wedges + texts:
        o.remove()

plt.close()


##############################################################################
# Alltime plots.
##############################################################################
def alltime_regs(present, absent, manual):
    f = plt.figure(figsize=figsize_square)
    f.suptitle(u'Обобщение на Всички Регистрации.')
    s = f.add_subplot(1,1,1)
    pie_array = [present, absent, manual]
    s.pie(pie_array, colors=['g', 'r', 'c'], labels=[u'Присъствия', u'Отсъствия', u'Ръчно\nзаписани'])
    f.savefig('generated_html/alltimeregs.png')
    plt.close()

def alltime_votes(y, n, abst, absent):
    f = plt.figure(figsize=figsize_square)
    f.suptitle(u'Обобщение на Всички Гласове.')
    s = f.add_subplot(1,1,1)
    pie_array = [y, n, abst, absent]
    s.pie(pie_array, colors=['g', 'r', 'c', 'k'], labels=[u'За', u'Против', u'Въздържали се', u'Отсъстващи'])
    f.savefig('generated_html/alltimevotes.png')
    plt.close()
