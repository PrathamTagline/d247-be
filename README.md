# d247-be

# run celery worker use following command
celery -A backend worker --loglevel=info --pool=solo

# run celery beat use following command 
celery -A backend beat --loglevel=info 