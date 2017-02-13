-- Setup Initial DB Schema v1.0.0

BEGIN;

-- Custom type used to support fuzzy dates in 'date' fields
-- eg. We may wish to enter 2016-06-03 as a precise date, but sometimes
-- we only know the year or year/month of recording/composition, and we still
-- want to be able to use the DATE type in Postgres. So by adding this custom
-- type, we're able to use DATE and also know the precision of the date entered
CREATE TYPE DATE_ACCURACY AS ENUM ('exact date', 'month', 'year');

CREATE TABLE album (
  id                      SERIAL PRIMARY KEY,
  title                   TEXT NOT NULL,
  release_date            DATE,
  release_date_accuracy   DATE_ACCURACY,
  total_discs             INTEGER NOT NULL,
  media                   TEXT NOT NULL
);

CREATE TABLE label (
  id    SERIAL PRIMARY KEY,
  name  TEXT NOT NULL UNIQUE
);

CREATE TABLE albums_labels (
  id            SERIAL PRIMARY KEY,
  fk_album_id   INTEGER REFERENCES album(id) NOT NULL,
  fk_label_id   INTEGER REFERENCES label(id) NOT NULL,
  catalog       TEXT,
  UNIQUE (fk_album_id, fk_label_id),
  UNIQUE (fk_label_id, catalog)
);

CREATE TABLE disc (
  id            SERIAL PRIMARY KEY,
  fk_album_id   INTEGER REFERENCES album(id) NOT NULL,
  disc_num      INTEGER NOT NULL,
  total_tracks  INTEGER NOT NULL
);

CREATE TABLE composition (
  id          SERIAL PRIMARY KEY,
  title       TEXT NOT NULL,
  total_mvmts INTEGER NOT NULL
);

CREATE TABLE catalog (
  id                  SERIAL PRIMARY KEY,
  fk_composition_id   INTEGER REFERENCES composition(id) NOT NULL,
  catalog_type        TEXT NOT NULL,
  -- Can't be integer, because of "numbers" like Opus "Posth."" --
  catalog_num         TEXT NOT NULL,
  catalog_sub_num     INTEGER
);

CREATE TABLE movement (
  id                SERIAL PRIMARY KEY,
  fk_composition_id INTEGER REFERENCES composition(id) NOT NULL,
  -- NULLable for single-movement works, where title will be in composition
  title             TEXT,
  mvmt_num          INTEGER NOT NULL
);

CREATE TABLE recording (
  id                        SERIAL PRIMARY KEY,
  type                      TEXT,
  recording_date            DATE,
  recording_date_accuracy   DATE_ACCURACY,
  -- enforce that, to enter a date, a date_accuracy value must also be specified
  CHECK ( recording_date IS NULL or recording_date_accuracy IS NOT NULL)
);

CREATE TABLE recordings_movements (
  id                SERIAL PRIMARY KEY,
  fk_recording_id   INTEGER REFERENCES recording(id) NOT NULL,
  fk_movement_id    INTEGER REFERENCES movement(id) NOT NULL
);

CREATE TABLE track (
  id              SERIAL PRIMARY KEY,
  fk_disc_id      INTEGER REFERENCES disc(id),
  fk_recording_id INTEGER REFERENCES recording(id) NOT NULL,
  track_num       INTEGER,
  track_length    INTEGER NOT NULL,
  audio_url       TEXT NOT NULL
);

CREATE TABLE person (
  id              SERIAL PRIMARY KEY,
  name_last       TEXT NOT NULL,
  name_first_plus TEXT NOT NULL
);

CREATE TABLE person_role (
  id    SERIAL PRIMARY KEY,
  type  TEXT NOT NULL
);

CREATE TABLE compositions_persons (
  id                  SERIAL PRIMARY KEY,
  fk_composition_id   INTEGER REFERENCES composition(id) NOT NULL,
  fk_person_id        INTEGER REFERENCES person(id) NOT NULL,
  fk_person_role_id   INTEGER REFERENCES person_role(id) NOT NULL
);
CREATE TABLE recordings_persons (
  id                  SERIAL PRIMARY KEY,
  fk_recording_id     INTEGER REFERENCES recording(id) NOT NULL,
  fk_person_id        INTEGER REFERENCES person(id) NOT NULL,
  fk_person_role_id   INTEGER REFERENCES person_role(id) NOT NULL
);

CREATE TABLE tracks_persons (
  id                  SERIAL PRIMARY KEY,
  fk_track_id         INTEGER REFERENCES track(id) NOT NULL,
  fk_person_id        INTEGER REFERENCES person(id) NOT NULL,
  fk_person_role_id   INTEGER REFERENCES person_role(id) NOT NULL
);

COMMIT;
