curl "http://www.parliament.bg/bg/plenaryst" 2> /dev/null |\
    grep "/bg/plenaryst/period/" |\
    perl -pe "s|.*?([12]\d\d\d-\d*).*|\1|" |\
    cat > data/periods_plenary_stenograms
