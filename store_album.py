# USAGE:
# python3 store_album.py relative/path/to/file.json
# TODO: add aggressive validation everywhere to make sure bad data never makes
# its way into the database

import psycopg2
import json
import sys
from datetime import datetime


def parse_data_from_file():
    """
    Parse JSON from file specified in CLI into dictionary

    Returns:
        dict -- album data
    """
    # get filename from CLI
    filename = sys.argv[1]

    # load JSON from file
    with open(filename) as data_file:
        data = json.load(data_file)

    return data


def construct_date_tuple(fuzzy_date):
    """
    Construct valid YYYY-MM-DD date string, as well as accuracy string
    from fuzzy date string.

    Why? So that we can still use the "DATE" type in the database, but
    preserving the disctinction between 2016-01-01 where we actually only
    know the year (2017), as compared to 2017-01-01 where we actually know
    that is is exactly January 1, 2017.

    Arguments:
        fuzzy_date {string} -- date in the following possible formats:
            YYYY-MM-DD, YYYY-MM, YYYY

    Returns:
        date + accuracy {tuple(str, str)} -- eg. ('2015-04-28', 'exact date')
            first element is a date string in YYYY-MM-DD format
            second element is a string of the these possible values:
                "exact date" - year, month, and day are all exact
                "month" - only year and month are accurate
                "year" - only year is accurate
    """
    for char in fuzzy_date:
        assert(char == '-' or char.isdigit())

    components = fuzzy_date.split('-')

    if len(components) == 3:
        return (fuzzy_date, 'exact date')

    elif len(components) == 2:
        return (
            datetime.strptime(fuzzy_date, '%Y-%m').strftime('%Y-%m-%d'),
            'month'
        )

    else:
        return (
            datetime.strptime(fuzzy_date, '%Y').strftime('%Y-%m-%d'),
            'year'
        )


def is_album_new(data, cursor):
    """
    Determine if the album is already in the database

    Unique identifiers for an album:
        label name + catalog
        label name + album title + release_date (if catalog is missing)
        label name + album title (if catalog AND release_date are both missing)

    'Label' is required.

    Args:
        data: dictionary of JSON data
        cursor: database cursor, coming from psycopg2

    Returns:
        boolean - True if album is new, False if album is already in DB
    """
    # uniquely identify an album by label name + catalog
    if 'catalog' in data['album']:
        cursor.execute("""
            SELECT a_l.id FROM albums_labels a_l
            JOIN label label
            ON label.id = a_l.fk_label_id
            WHERE label.name = %s
            AND a_l.catalog = %s
        """, (data['album']['label'], data['album']['catalog']))

    # uniquely identify an album by
    # label name + album title + release_date (if catalog is missing)
    elif 'release_date' in data['album']:
        release_date, release_date_accuracy = construct_date_tuple(
            data['album']['release_date'])

        cursor.execute("""
            SELECT a_l.id FROM albums_labels a_l
            JOIN label label
            ON label.id = a_l.fk_label_id
            JOIN album album
            ON album.id = a_l.fk_album_id
            WHERE label.name = %s
            AND album.title = %s
            AND release_date = %s
            AND release_date_accuracy = %s
        """, (
            data['album']['label'],
            data['album']['title'],
            release_date,
            release_date_accuracy
        ))

    # uniquely identify an album by
    # label name + album title (if catalog AND release_date are both missing)
    else:
        cursor.execute("""
            SELECT a_l.id FROM albums_labels a_l
            JOIN label label
            ON label.id = a_l.fk_label_id
            JOIN album album
            ON album.id = a_l.fk_album_id
            WHERE label.name = %s
            AND album.title = %s
        """, (
            data['album']['label'],
            data['album']['title']
        ))

    return not bool(cursor.fetchone())


def process_album(data, cursor):
    label_id = add_label_and_get_id(data, cursor)
    # print(label_id)
    # album_id = add_album_and_get_id(data, label_id, cursor)
    # add_discs(data, album_id, cursor)


def add_label_and_get_id(data, cursor):
    """if label already exists, get label id, otherwise insert and get label id
    """
    cursor.execute("SELECT id FROM label WHERE name = %s",
                   (data['album']['label'],))
    try:
        label_id = cursor.fetchone()[0]
    except TypeError:
        cursor.execute("INSERT INTO label (name) VALUES (%s) RETURNING id",
                       (data['album']['label'],))
        label_id = cursor.fetchone()[0]
    return label_id


def add_album_and_get_id(data, label_id, cursor):
    pass


def add_discs(data, album_id, cursor):
    pass


def main():
    # open connection and fetch cursor to database
    connection = psycopg2.connect('dbname=classicast user=postgres')
    cursor = connection.cursor()

    data = parse_data_from_file()

    if is_album_new(data, cursor):
        process_album(data, cursor)
    else:
        print("""This album already exists in the system! Please edit the
            existing data.""")

    # Make the changes to the database persistent
    connection.commit()

    # Close communication with the database
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()


# # Add album information
# #######################
# # If the album already exists, get album id
# # otherwise insert album, albums_labels, and get album id
# # Unique identifiers for an album:
# # label + catalog
# # label + name + release_date (if catalog is missing)
# # label + name (if catalog AND release_date are both missing)
# if 'catalog' in data['album']:
#     cur.execute("""
#         SELECT a.id FROM album a
#         JOIN albums_labels a_l
#         ON a.id = a_l.fk_album_id
#         WHERE a_l.catalog = %s
#     """, (data['album']['catalog'],))
# elif 'release_date' in data['album']:
#     # TODO: query to identify album by label + name + release_date
#     pass
# else:
#     # TODO: query to identify album by label + name
#     pass

# try:
#     album_id = cur.fetchone()[0]
# except:
#     cur.execute("""
#         INSERT INTO album (title, total_discs, media) VALUES (%s, %s, %s)
#         RETURNING id
#     """, (
#         data['album']['title'],
#         data['album']['total_discs'],
#         data['album']['media']
#     ))
#     album_id = cur.fetchone()[0]
#     # Insert optional release_date field
#     if 'release_date' in data['album']:
#         # TODO: parse the release_date in data to determine accuracy
#         # (year, month, day)
#         # TODO: create a time object from the release_date field in YYYY-MM-DD
#         # format
#         # TODO: INSERT release date and precision values into DB
#         pass
#     cur.execute("""
#         INSERT INTO albums_labels (fk_album_id, fk_label_id, catalog)
#         VALUES (%s, %s, %s)
#     """, (album_id, label_id, data['album']['catalog']))
# # print(album_id)

# # Add discs
# # TODO: make this dependent on the album being new, and not already in the system
# ########################
# total_discs = data['album']['total_discs']
# discs = data['discs']
# for disc_num in range(1, total_discs+1):
#     total_tracks = discs[str(disc_num)]['total_tracks']
#     cur.execute("""
#         INSERT INTO disc (fk_album_id, disc_num, total_tracks)
#         VALUES (%s, %s, %s)
#     """, (album_id, disc_num, total_tracks))


