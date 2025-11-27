# In start.sh, you need the correct project name
gunicorn DjangoCart.wsgi:application --bind 0.0.0.0:8000