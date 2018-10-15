FROM python:3.6

ADD         requirements.txt /app/
WORKDIR     /app

RUN         pip install -r /app/requirements.txt
ADD         . /app

EXPOSE      80
ENV         FLASK_APP "manage.py"
ENV         AWS_DEFAULT_REGION "us-east-1"

CMD ["flask", "run", "-h", "0.0.0.0", "-p", "80"]
