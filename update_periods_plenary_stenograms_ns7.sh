curl "http://www.parliament.bg/bg/plenaryst/ns/7/period/" 2> /dev/null |\
    grep "/bg/plenaryst/ns/7/period/" |\
    perl -pe "s|.*?([12]\d\d\d-\d*).*|\1|" |\
    cat > data/periods_plenary_stenograms
