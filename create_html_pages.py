from mako.template import Template
from mako.lookup import TemplateLookup
from stenograms_to_db import *
import os
import cPickle

os.system('cp -r htmlkickstart/css generated_html/css')
os.system('cp -r htmlkickstart/js generated_html/js')
os.system('cp htmlkickstart/style.css generated_html/style.css')

stenograms_dump = open('data/stenograms_dump', 'r')
stenograms = cPickle.load(stenograms_dump)
stenograms_dump.close()

templates = TemplateLookup(directories=['mako_templates'],
                           input_encoding='utf-8',
                           output_encoding='utf-8')

per_stenogram_template = templates.get_template('stenogramN_template.html')
for st in stenograms.values():
    with open('generated_html/stenogram%s.html'%st.date.strftime('%Y%m%d'), 'w') as html_file:
        html_file.write(per_stenogram_template.render(stenogram=st))

all_stenograms_template = templates.get_template('stenograms_template.html')
with open('generated_html/stenograms.html', 'w') as html_file:
    html_file.write(all_stenograms_template.render(stenograms=stenograms))

