for i in `dir generated_html/*png`; do cat $i | pngquant -ordered 63 > $i.tmp; mv $i.tmp $i; done;
