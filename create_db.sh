dropdb parlamentarenkontrol -U parlamentarenkontrol
createdb -E UTF8 parlamentarenkontrol -U parlamentarenkontrol

psql parlamentarenkontrol -U parlamentarenkontrol <<SQL
CREATE TABLE stenograms (
       stenogram_date  date PRIMARY KEY,
       text            text[],
       vote_line_nb    integer[],
       problem         bool,
       original_url    text UNIQUE
);

CREATE TABLE vote_sessions (
       stenogram_date  date REFERENCES stenograms (stenogram_date),
       session_number  integer,
       description     text,
       PRIMARY KEY (stenogram_date, session_number)
);

CREATE TABLE parties (
       party_name  text PRIMARY KEY
);

CREATE TABLE mps (
       mp_name          text PRIMARY KEY,
       orig_party_name  text REFERENCES parties (party_name),
       email            text,
       original_url     text UNIQUE
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


 CREATE EXTENSION first_last_agg;

SQL
