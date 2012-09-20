rm -f data/IDs_MPs
curl http://www.parliament.bg/bg/MP 2> /dev/null | grep ">Информация" | sort | cut -d'"' -f6 | cut -d'/' -f4 | grep -o '[0-9]*' | sort -n > data/IDs_MPs
