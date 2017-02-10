-- Seed data: First Albums!
-- TODO: use postgres variables to avoid duplicate queries and text repeats

-- First Album
-------------------------------------------------------------------------------
WITH album_rows AS (
  INSERT INTO album (title, total_discs, media)
  VALUES ('The Art of Nikolai Golovanov Volume I', 1, 'CD')
  RETURNING id
),
label_rows AS (
  INSERT INTO label (name) VALUES ('Arlecchino') RETURNING id
)
INSERT INTO albums_labels (fk_album_id, fk_label_id, catalog) VALUES (
  (SELECT id FROM album_rows),
  (SELECT id FROM label_rows),
  'ARL 32'
);


INSERT INTO disc (fk_album_id, disc_num, total_tracks) VALUES (
  (SELECT id FROM album WHERE title = 'The Art of Nikolai Golovanov Volume I'),
  1,
  5
);

############


INSERT INTO composition (title, total_mvmts) VALUES
  ('Prometheus: The Poem of Fire', 1),
  ('The Poem of Ecstasy', 1),
  ('Piano Concerto in f-sharp minor', 3);


INSERT INTO catalog (fk_composition_id, catalog_type, catalog_num) VALUES
  (
    (SELECT id FROM composition WHERE title = 'Prometheus: The Poem of Fire'),
    'Opus',
    60
  ),
  (
    (SELECT id FROM composition WHERE title = 'The Poem of Ecstasy'),
    'Opus',
    54
  ),
  (
    (SELECT id FROM composition WHERE title = 'Piano Concerto in f-sharp minor'),
    'Opus',
    20
  );


INSERT INTO movement (fk_composition_id, title, mvmt_num) VALUES
  (
    (SELECT id FROM composition WHERE title = 'Prometheus: The Poem of Fire'),
    NULL,
    1
  ),
  (
    (SELECT id FROM composition WHERE title = 'The Poem of Ecstasy'),
    NULL,
    1
  ),
  (
    (SELECT id FROM composition WHERE title = 'Piano Concerto in f-sharp minor'),
    'I. Allegro',
    1
  ),
  (
    (SELECT id FROM composition WHERE title = 'Piano Concerto in f-sharp minor'),
    'II. Andante',
    2
  ),
  (
    (SELECT id FROM composition WHERE title = 'Piano Concerto in f-sharp minor'),
    'III. Allegro moderato',
    3
  );


WITH recording_rows AS (
  INSERT INTO recording (date, date_accuracy) VALUES ('1947-01-01', 'year') RETURNING id
)
INSERT INTO recordings_movements (fk_recording_id, fk_movement_id)
VALUES (
  (SELECT id from recording_rows),
  (SELECT id from movement WHERE fk_composition_id = (
    SELECT id from composition WHERE title = 'Prometheus: The Poem of Fire'
  ))
);


WITH recording_rows AS (
  INSERT INTO recording (date, date_accuracy) VALUES ('1952-01-01', 'year') RETURNING id
)
INSERT INTO recordings_movements (fk_recording_id, fk_movement_id)
VALUES (
  (SELECT id from recording_rows),
  (SELECT id from movement WHERE fk_composition_id = (
    SELECT id from composition WHERE title = 'The Poem of Ecstasy'
  ))
);


WITH recording_rows AS (
  INSERT INTO recording (date, date_accuracy) VALUES ('1946-01-01', 'year') RETURNING id
)
INSERT INTO recordings_movements (fk_recording_id, fk_movement_id)
VALUES
  (
    (SELECT id from recording_rows),
    (
      SELECT id from movement
      WHERE fk_composition_id = (
        SELECT id from composition WHERE title = 'Piano Concerto in f-sharp minor'
      )
      AND mvmt_num = 1
    )
  ),
  (
    (SELECT id from recording_rows),
    (
      SELECT id from movement
      WHERE fk_composition_id = (
        SELECT id from composition WHERE title = 'Piano Concerto in f-sharp minor'
      )
      AND mvmt_num = 2
    )
  ),
  (
    (SELECT id from recording_rows),
    (
      SELECT id from movement
      WHERE fk_composition_id = (
        SELECT id from composition WHERE title = 'Piano Concerto in f-sharp minor'
      )
      AND mvmt_num = 3
    )
  );

#########


-- Second Album
-------------------------------------------------------------------------------
WITH album_rows AS (
  INSERT INTO album (title, total_discs, media) VALUES (
    'The Art of Nikolai Golovanov Volume III', 1, 'CD'
  )
  RETURNING id
),
label_rows AS (
  SELECT id from label WHERE name = 'Arlecchino'
)
INSERT INTO albums_labels (fk_album_id, fk_label_id, catalog) VALUES (
  (SELECT id FROM album_rows),
  (SELECT id FROM label_rows),
  'ARL 101'
);