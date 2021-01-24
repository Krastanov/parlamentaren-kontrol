download () {
echo Assembly $2
curl "https://www.parliament.bg/bg/plenaryst/ns/$1/period/" 2> /dev/null |\
    grep -P "/bg/plenaryst/ns/$1/period/\d" |\
    perl -pe "s|.*?([12]\d\d\d-\d*).*|\1|" |\
    cat > craw_data/periods_plenary_stenograms_$2

rm -f craw_data/IDs_plenary_stenograms_$2
for i in `cat craw_data/periods_plenary_stenograms_$2`
do
    echo $i
    curl "https://www.parliament.bg/bg/plenaryst/ns/$1/period/"$i 2> /dev/null |\
        grep "/bg/plenaryst/ns/$1/ID/" |\
        perl -pe "s|.*?/ID/(\d*).*|\1|" |\
        cat >> craw_data/IDs_plenary_stenograms_$2
done
}

# XXX Hardcoded values
download 7 41
download 50 42
download 51 43
download 52 44
