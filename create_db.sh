dropdb parlamentarenkontrol -U parlamentarenkontrol
createdb -E UTF8 parlamentarenkontrol -U parlamentarenkontrol

psql parlamentarenkontrol -U parlamentarenkontrol <<SQL
CREATE TABLE stenograms (
       stenogram_date  date PRIMARY KEY,
       text            text[],
       vote_line_nb    integer[],
       problem         bool,
       original_url    text UNIQUE NOT NULL
);

CREATE TABLE vote_sessions (
       stenogram_date  date REFERENCES stenograms (stenogram_date),
       session_number  integer,
       description     text,
       time            time,
       PRIMARY KEY (stenogram_date, session_number)
);

CREATE TABLE parties (
       party_name  text PRIMARY KEY
);

CREATE TABLE mps (
       mp_name  text PRIMARY KEY,
       email    text[]
);

CREATE TABLE parliaments (
       parliament  integer PRIMARY KEY
);

CREATE TABLE elections (
       mp_name          text REFERENCES mps (mp_name),
       orig_party_name  text REFERENCES parties (party_name),
       parliament       integer REFERENCES parliaments (parliament),
       original_url     text UNIQUE NOT NULL,
       PRIMARY KEY (mp_name, orig_party_name, parliament)
);

CREATE TYPE mp_vote_enum AS ENUM ('yes', 'no', 'abstain', 'absent');
CREATE TABLE mp_votes (
       mp_name         text REFERENCES mps (mp_name),
       with_party      text REFERENCES parties (party_name),
       stenogram_date  date,
       session_number  integer,
       vote            mp_vote_enum,
       PRIMARY KEY (mp_name, stenogram_date, session_number),
       FOREIGN KEY (stenogram_date, session_number) REFERENCES vote_sessions (stenogram_date, session_number)
);

CREATE TYPE mp_reg_enum AS ENUM ('present', 'absent', 'manually_registered');
CREATE TABLE mp_reg (
       mp_name         text REFERENCES mps (mp_name),
       with_party      text REFERENCES parties (party_name),
       stenogram_date  date REFERENCES stenograms (stenogram_date),
       reg             mp_reg_enum,
       PRIMARY KEY (mp_name, stenogram_date)
);

CREATE TABLE party_votes (
       party_name      text REFERENCES parties (party_name),
       stenogram_date  date,
       session_number  integer,
       yes             integer,
       no              integer,
       abstain         integer,
       total           integer,
       PRIMARY KEY (party_name, stenogram_date, session_number),
       FOREIGN KEY (stenogram_date, session_number) REFERENCES vote_sessions (stenogram_date, session_number)
);

CREATE TABLE party_reg (
       party_name      text REFERENCES parties (party_name),
       stenogram_date  date REFERENCES stenograms (stenogram_date),
       present         integer,
       expected        integer,
       PRIMARY KEY (party_name, stenogram_date)
);

CREATE TABLE bills (
       bill_name       text,
       bill_signature  text PRIMARY KEY,
       bill_date       date,
       original_url    text UNIQUE NOT NULL
);

CREATE TABLE bill_authors (
       bill_signature  text REFERENCES bills (bill_signature),
       bill_author     text REFERENCES mps (mp_name),
       PRIMARY KEY (bill_signature, bill_author)
);

CREATE TABLE bills_by_government (
       bill_signature  text PRIMARY KEY REFERENCES bills (bill_signature)
);

CREATE TYPE bill_event AS ENUM ('proposed_1st', 'proposed_2nd',
                                'accepted_1st', 'accepted_2nd',
                                'rejected_1st', 'rejected_2nd',
                                'retracted',
                                'vetoed',
                                'proposed_after_veto',
                                'accepted_after_veto',
                                'challenged_after_veto'
                                );
CREATE TABLE bill_history (
    bill_signature  text REFERENCES bills (bill_signature),
    event_date      date,
    event           bill_event,
    PRIMARY KEY (bill_signature, event_date, event)
);

CREATE TABLE laws (
    bill_signature  text PRIMARY KEY REFERENCES bills (bill_signature),
    sg_issue        int,
    sg_year         date,
    text            text
);


CREATE INDEX mp_votes_BY_stenogram_date_session_number ON mp_votes (stenogram_date, session_number);


CREATE EXTENSION first_last_agg;

SQL
