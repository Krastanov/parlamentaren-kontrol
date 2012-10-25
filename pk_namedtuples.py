from collections import namedtuple

stgram_tuple = namedtuple('stgram_tuple', ['date', 'text_lines', 'in_text_votes',
                                           'reg_by_name_dict',
                                            # {rep_tuple: registered_bool}
                                           'reg_by_party_dict',
                                            # {name_string: reg_stats_per_party_tuple}
                                           'sessions',
                                            # [sesion_tuple]
                                           ])

rep_tuple = namedtuple('rep_tuple', ['name', 'party'])

session_tuple = namedtuple('session_tuple', ['description',
                                             'votes_by_name_dict',
                                                # {rep_tuple: vote_code_string}
                                             'votes_by_party_dict',
                                                # {name_string: vote_stats_per_party_tuple}
                                             ])

reg_stats_per_party_tuple = namedtuple('reg_stats_per_party_tuple', ['present', 'expected'])
vote_stats_per_party_tuple = namedtuple('vote_stats_per_party_tuple', ['yes', 'no', 'abstained', 'total'])
