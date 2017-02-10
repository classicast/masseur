# Masseur
============
Service to massage album and track data and put it into the database in the right format.
This service is responsible for injesting new albums and tracks that will be used by ClassiCast

### Startup Instructions (on OS X)
1. Install Postgres App
1. Setup DB:
  1. `psql`
    1. `create database classicast owner postgres`
    1. `\l` (to confirm the database is there)
  1. Install initial schema: `psql -U postgres -d classicast -a -f migrations/migration0001.sql`
2. Install Brew
3. `brew install python3`
4. `PATH=$PATH:/Applications/Postgres.app/Contents/Versions/latest/bin pip3 install psycopg2`

### FEATURES TODO:
- finish 'store_album.py' python script so I can upload a complete album release based solely on its JSON representation

### INFRASTRUCTURE TODO:
- local installation of psycopg2 instead of global
- docker
- tests
- setup migration tool
- move initial DB schema setup sql script out of this repo