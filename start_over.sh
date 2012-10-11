rm -rf data/*
rm -rf log/*
rm -rf generated_html
mkdir generated_html
echo "Creating empty database (you should have already ran \`sudo sh create_db.sh\`)"
echo "Update all IDs of MPs"
sh update_IDs_MPs.sh
echo "Download MPs emails"
python download_MP_mails.py
echo "Update all periods for which there is a record."
sh update_all_periods.sh
echo "Update all IDs of plenary stenograms."
sh update_IDs_plenary_stenograms_after_2011.sh
echo "Download and parse the stenograms."
python stenograms_to_db.py
#echo "Create the html pages."
#python create_html_pages.py
#echo "Optimize the png files."
#sh optimize_png.sh
