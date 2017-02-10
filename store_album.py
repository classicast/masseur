# USAGE:
# python3 store_album.py

import psycopg2

conn = psycopg2.connect('dbname=classicast user=postgres')
cur = conn.cursor()

# TODO: parse json file to get this
# album_info = {
#   "album": {
#     "title": "The Art of Nikolai Golovanov Volume I",
#     "label": "Arlecchino",
#     "catalog": "ARL 32",
#     "media": "CD",
#     "total_discs": 1
#   },
#   "discs": {
#     "1": {
#       "total_tracks": 5
#     }
#   }
# }

album_info = {
  "album": {
    "title": "Etelka Freund",
    "label": "Pearl",
    "catalog": "GEMM CDS 9193",
    "release_date": "1996-05-21",
    "media": "CD",
    "total_discs": 2
  },
  "discs": {
    "1": {
      "total_tracks": 35
    },
    "2": {
      "total_tracks": 24
    }
  }
}

# Add label information
#######################
# if label already exists, get label id, otherwise insert and get label id
cur.execute("SELECT id FROM label WHERE name = %s",
    (album_info['album']['label'],))
try:
    label_id = cur.fetchone()[0]
except TypeError:
    cur.execute("INSERT INTO label (name) VALUES (%s) RETURNING id",
        (album_info['album']['label'],))
    label_id = cur.fetchone()[0]
# print(label_id)

# Add album information
#######################
# If the album already exists, get album id
# otherwise insert album, albums_labels, and get album id
# Unique identifiers for an album:
# label + catalog
# label + name + release_date (if catalog is missing)
# label + name (if catalog AND release_date are both missing)
if 'catalog' in album_info['album']:
    cur.execute("""
        SELECT a.id FROM album a
        JOIN albums_labels a_l
        ON a.id = a_l.fk_album_id
        WHERE a_l.catalog = %s
    """, (album_info['album']['catalog'],))
elif 'release_date' in album_info['album']:
    # TODO: query to identify album by label + name + release_date
    pass
else:
    # TODO: query to identify album by label + name
    pass

try:
    album_id = cur.fetchone()[0]
except:
    cur.execute("""
        INSERT INTO album (title, total_discs, media) VALUES (%s, %s, %s)
        RETURNING id
    """, (
        album_info['album']['title'],
        album_info['album']['total_discs'],
        album_info['album']['media']
    ))
    album_id = cur.fetchone()[0]
    # Insert optional release_date field
    if 'release_date' in album_info['album']:
        # TODO: parse the release_date in album_info to determine accuracy
        # (year, month, day)
        # TODO: create a time object from the release_date field in YYYY-MM-DD
        # format
        # TODO: INSERT release date and precision values into DB
        pass
    cur.execute("""
        INSERT INTO albums_labels (fk_album_id, fk_label_id, catalog)
        VALUES (%s, %s, %s)
    """, (album_id, label_id, album_info['album']['catalog']))
# print(album_id)

# Add discs
########################
total_discs = album_info['album']['total_discs']
discs = album_info['discs']
for disc_num in range(1, total_discs+1):
    total_tracks = discs[str(disc_num)]['total_tracks']
    cur.execute("""
        INSERT INTO disc (fk_album_id, disc_num, total_tracks)
        VALUES (%s, %s, %s)
    """, (album_id, disc_num, total_tracks))

# Make the changes to the database persistent
conn.commit()

# Close communication with the database
cur.close()
conn.close()
