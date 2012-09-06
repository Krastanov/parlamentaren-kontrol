rm -rf data
mkdir data
echo "Update all periods for which there is a record."
sh update_all_periods.sh
echo "Update all IDs of plenary stenograms."
sh update_IDs_plenary_stenograms_after_2012.sh
echo "Download and parse the stenograms."
python stenograms_to_db.py > /dev/null
echo "Create the html pages."
python create_html_pages.py
