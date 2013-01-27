rm -f data/IDs_plenary_stenograms
for i in `cat data/periods_plenary_stenograms`
do
    curl "http://www.parliament.bg/bg/plenaryst/ns/7/period/"$i 2> /dev/null |\
        grep "/bg/plenaryst/ns/7/ID/" |\
        perl -pe "s|.*?/ID/(\d*).*|\1|" |\
        cat >> data/IDs_plenary_stenograms
done
