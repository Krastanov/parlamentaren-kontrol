### List all parliaments appearing in MP records

Appearing as "current" 

```bash
xmllint --xpath "string(//schema/ParliamentaryActivity/ParliamentaryStructure/ParliamentaryStructureName/@value)" * 2> /dev/null | sort | uniq
```

### Fix xls to xlsx file extentions

```fish
for f in (file *.xls | grep "2007+" | cut -d":" -f1); mv $f $f"x"; end
```
