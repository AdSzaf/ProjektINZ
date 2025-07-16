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


dockerstuff
docker-compose up
docker-compose up --build
docker-compose down -v
docker-compose exec backend python manage.py migrate
