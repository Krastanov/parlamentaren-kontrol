curl "http://www.parliament.bg/bg/plenaryst/ns/7/period/" 2> /dev/null |\
    grep -P "/bg/plenaryst/ns/7/period/\d" |\
    perl -pe "s|.*?([12]\d\d\d-\d*).*|\1|" |\
    cat > data/periods_plenary_stenograms_41
curl "http://www.parliament.bg/bg/plenaryst/ns/50/period/" 2> /dev/null |\
    grep -P "/bg/plenaryst/ns/50/period/\d" |\
    perl -pe "s|.*?([12]\d\d\d-\d*).*|\1|" |\
    cat > data/periods_plenary_stenograms_42


rm -f data/IDs_plenary_stenograms_41
for i in `cat data/periods_plenary_stenograms_41`
do
    curl "http://www.parliament.bg/bg/plenaryst/ns/7/period/"$i 2> /dev/null |\
        grep "/bg/plenaryst/ns/7/ID/" |\
        perl -pe "s|.*?/ID/(\d*).*|\1|" |\
        cat >> data/IDs_plenary_stenograms_41
done
rm -f data/IDs_plenary_stenograms_42
for i in `cat data/periods_plenary_stenograms_42`
do
    curl "http://www.parliament.bg/bg/plenaryst/ns/50/period/"$i 2> /dev/null |\
        grep "/bg/plenaryst/ns/50/ID/" |\
        perl -pe "s|.*?/ID/(\d*).*|\1|" |\
        cat >> data/IDs_plenary_stenograms_42
done
