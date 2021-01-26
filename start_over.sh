rm -rf data/*
rm -rf log/*
rm -rf generated_html
mkdir generated_html
echo "Creating empty database"
sh create_db.sh
echo "Download MPs details"
# TODO for i in (seq 1 2984); echo $i; wget -q https://www.parliament.bg/export.php/bg/csv/MP/$i; sleep 0.2; end;
echo "Parse MPs details"
python craw_mps_data.py
echo "Update all IDs of plenary stenograms."
sh update_periods_plenary_stenograms.sh
echo "Download and parse the stenograms."
python craw_stenograms.py
echo "Create the html pages."
python create_html_pages.py
echo "Optimize the png files."
sh optimize_png.sh
