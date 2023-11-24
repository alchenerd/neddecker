docker start redis_neddecker || docker run -p 6379:6379 --name redis_neddecker -d redis:5
python manage.py syncdb
python manage.py runserver
