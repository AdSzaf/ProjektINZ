uruchamianie lokalnie backend

cd backend
source venv/bin/activate
python manage.py migrate
python manage.py runserver


uruchamianie frontu lokalnie

cd frontend

yarn install
yarn dev

ew. yarn start

do postgres

psql -U postgres
CREATE DATABASE inz_project;
pg admin działa też.
