from mako.template import Template
from stenograms_to_db import *
import shelve
import os

os.system('cp -r htmlkickstart/css generated_html/css')
os.system('cp -r htmlkickstart/js generated_html/js')
os.system('cp htmlkickstart/style.css generated_html/style.css')

stenograms_dump = shelve.open('data/stenograms_dump')
stenograms = stenograms_dump['stenograms']

per_stenogram_template = Template(filename='per_stenogram_template.html',
                                  input_encoding='utf-8',
                                  output_encoding='utf-8')

for k, st in stenograms.items():
    html_file = open('generated_html/stenogram%s.html'%k, 'w')
    html_file.write(per_stenogram_template.render(stenogram=st))



