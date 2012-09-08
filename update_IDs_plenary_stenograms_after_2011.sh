rm -f /data/IDs_plenary_stenograms
for i in `cat data/periods_plenary_stenograms`
do
    if [ "`echo $i | cut -d"-" -f1`" -ge "2011" ]
    then
        curl "http://www.parliament.bg/bg/plenaryst/period/"$i 2> /dev/null |\
            grep "/bg/plenaryst/ID/" |\
            perl -pe "s|.*?/ID/(\d*).*|\1|" |\
            cat >> data/IDs_plenary_stenograms
    fi
done
sort data/IDs_plenary_stenograms | uniq > data/IDs_plenary_stenograms_tmp
mv data/IDs_plenary_stenograms_tmp data/IDs_plenary_stenograms
