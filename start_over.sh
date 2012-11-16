rm -rf data/*
rm -rf log/*
rm -rf generated_html
mkdir generated_html
echo "Creating empty database"
sh create_db.sh
echo "Update all IDs of MPs"
sh update_IDs_MPs.sh
echo "Download MPs details"
python craw_mps_data.py
echo "Update all periods for which there is a record."
sh update_all_periods.sh
echo "Update all IDs of plenary stenograms."
sh update_IDs_plenary_stenograms_after_2011.sh
echo "Download and parse the stenograms."
python craw_stenograms.py
echo "Create the html pages."
python create_html_pages.py
echo "Optimize the png files."
sh optimize_png.sh
