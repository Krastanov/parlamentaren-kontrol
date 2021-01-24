### List all parliaments appearing in MP records

Appearing as "current" 

```bash
xmllint --xpath "string(//schema/ParliamentaryActivity/ParliamentaryStructure/ParliamentaryStructureName/@value)" * 2> /dev/null | sort | uniq
```
