-- Populate Supported Person Roles

BEGIN;

INSERT INTO person_role (type) VALUES ('composer');
INSERT INTO person_role (type) VALUES ('conductor');
INSERT INTO person_role (type) VALUES ('ensemble');
INSERT INTO person_role (type) VALUES ('soloist');

COMMIT;