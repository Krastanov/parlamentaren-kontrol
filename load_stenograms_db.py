from stenograms_to_db import *
import shelve

stenograms_dump = shelve.open('data/stenograms_dump')
stenograms = stenograms_dump['stenograms']

for k, st in stenograms.items():
    print '========================================'
    print k
    print st.date

    for issue, parties in st.by_party_votes.items()[:2]:
        print ' %s: %s' % (issue.kind, issue.details)
        for party, votes in parties.items()[:2]:
            print '  %s' % party
            print '   %s' % str(votes)
        print '  ...'
    print ' ...'
    for MP, MP_votes in st.by_name_votes.items()[:5]:
        print '  # %s from %s' % MP, ', '.join(MP_votes)
    print '  # ...'



