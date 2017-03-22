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
    album_id = add_album_and_get_id(data, label_id, cursor)
    add_discs(data, album_id, cursor)

    persons_subm_to_db_id_map = add_persons(data, cursor)
    add_compositions(data, persons_subm_to_db_id_map, cursor)

    # add_recordings(data, cursor)
    # add_tracks(data, cursor)


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
    """adds a new album, and returns its ID"""

    # Construct optional release_date and release_date_accuracy values
    date = None
    accuracy = None
    if 'release_date' in data['album']:
        date, accuracy = construct_date_tuple(data['album']['release_date'])
    cursor.execute("""
        INSERT INTO album (title, release_date, release_date_accuracy,
                           total_discs, media) VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data['album']['title'],
        date,
        accuracy,
        data['album']['total_discs'],
        data['album']['media']
    ))
    album_id = cursor.fetchone()[0]
    cursor.execute("""
        INSERT INTO albums_labels (fk_album_id, fk_label_id, catalog)
        VALUES (%s, %s, %s)
    """, (album_id, label_id, data['album']['catalog']))
    return album_id


def add_discs(data, album_id, cursor):
    """add discs to DB"""
    total_discs = data['album']['total_discs']
    discs = data['discs']
    for disc_num in range(1, total_discs+1):
        total_tracks = discs[str(disc_num)]['total_tracks']
        cursor.execute("""
            INSERT INTO disc (fk_album_id, disc_num, total_tracks)
            VALUES (%s, %s, %s)
        """, (album_id, disc_num, total_tracks))


def add_persons(data, cursor):
    """ Add persons to database """
    persons_subm_to_db_id_map = {}
    persons = data.get('persons')
    for subm_id, person in persons.items():
        persons_subm_to_db_id_map[subm_id] = add_person(person, cursor)
    return persons_subm_to_db_id_map


def add_person(person, cursor):
    """ get person id, and if not already in DB, add person to the DB
    """
    cursor.execute("""
        SELECT id FROM person (name_last, name_first_plus, group_name)
        WHERE name_last = %s
        AND name_first_plus = %s
        AND group_name = %s
    """, (
        person.get('name_last'),
        person.get('name_first_plus'),
        person.get('group_name'))
    )

    try:
        person_id = cursor.fetchone()[0]
    except TypeError:
        cursor.execute("""
            INSERT INTO person (name_last, name_first_plus, group_name)
                 VALUES (%s, %s, %s)
                 RETURNING id
        """, (
            person.get('name_last'),
            person.get('name_first_plus'),
            person.get('group_name')
        ))
        person_id = cursor.fetchone()[0]
    return person_id


def add_compositions(data, persons_subm_to_db_id_map, cursor):
    """ Add compositions to database """
    compositions = data.get('compositions')
    for key, composition in compositions.items():
        add_composition(data, composition, persons_subm_to_db_id_map, cursor)


def add_composition(data, composition, persons_subm_to_db_id_map, cursor):
    """ Add composition to database
    #
    # Unhandled cases (for now, at least):
    #   - Anything that doesn't have enough data to be matched using above
    #   uniqueness definitions, such as:
    #       - Anonymous Composers
    #       - No Title
    #       - Atonal music that is unpublished without catalog number
    #       - Derivative works of any kind (where person is not "Composer")
    """
    title = composition.get('title')
    movements = composition.get('movements')
    total_movements = len(movements) if movements else 1

    # Get composer_db_id
    # TODO: abstract into separate method
    # TODO: support more than just "composer" person related to composition,
    # should also support 'arranger', 'transcriber', etc... (other valid
    # "composer-like" roles)
    persons = composition.get('persons')
    composer_submission_id = next(
        (p.submission_id for p in persons if p['type'] == 'composer'), None)
    composer_db_id = persons_subm_to_db_id_map.get(composer_submission_id)

    catalogs = composition.get('catalogs')
    if catalogs:
        first_catalog = catalogs[0]
        catalog_type = first_catalog.get('catalog_type')
        catalog_num = first_catalog.get('catalog_num')
        catalog_sub_num = first_catalog.get('catalog_sub_num')

        # Unique Identifier of a Composition
        # Version 1 - Composition with Catalog Info
        #     Composition Persons (i.e. Composer(s), Arranger(s), etc.)
        #     Title
        #     Total # of Movements
        #     Catalog (just the first one is enough)
        cursor.execute("""
            SELECT (id) from composition as composition
            JOIN compositions_persons as person
            ON composition.id = compositions_persons.fk_composition_id
            JOIN person as person
            ON person.id = compositions_persons.fk_person_id
            JOIN person_role as person_role
            ON person_role.id = compositions_persons.fk_person_role_id
            JOIN catalog as catalog
            ON composition.id = fk_composition_id
            WHERE person_role.type = 'composer'
            AND person.id = %s
            AND composition.title = %s
            AND composition.total_mvmts = %s
            AND catalog.catalog_type = %s
            AND catalog.catalog_num = %s
            AND catalog.catalog_sub_num = %s
        """, (
            composer_db_id,
            title,
            total_movements,
            catalog_type,
            catalog_num,
            catalog_sub_num)
        )
        composition_id = cursor.fetchone()[0]

    else:
        # Unique Identifier of a Composition
        # Version 2 - Composition Lacking Catalog Info
        #     Composition Persons (i.e. Composer(s), Arranger(s), etc.)
        #     Title
        #     Total # of Movements
        #     Key (or mode)
        #
        #     Date of Composition (if date range, choose earliest date)
        #     AND / OR
        #     First Publication Date (if date range, choose earliest date)
        pass

    # If no composition is found, insert all the data and return the
    # composition_id
    #
    #   insert composition table row, returning composition_id
    #   for person in persons:
    #       add_composition_person(data, person, composition_id)

    #   for catalog in catalogs:
    #       add_catalog(catalog, composition_id)

    #   for movement in movements:
    #       add_movement(movement, composition_id)


def add_catalog(data, cursor):
    pass


def add_movements(data, cursor):
    pass


def add_recordings(data, cursor):
    pass


def add_tracks(data, cursor):
    pass


def main():
    # open connection and fetch cursor to database
    connection = psycopg2.connect('dbname=classicast user=postgres')
    cursor = connection.cursor()

    data = parse_data_from_file()

    try:
        if is_album_new(data, cursor):
            process_album(data, cursor)

            # Make the changes to the database persistent
            connection.commit()
        else:
            print('This album already exists in the system!' +
                  ' Please edit the existing data.')
    except Exception as exception_instance:
        # rollback any changes if error is encountered in the process of adding
        # album information to the database
        connection.rollback()
        raise exception_instance
    finally:
        # Close communication with the database
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
