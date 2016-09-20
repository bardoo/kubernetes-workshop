FROM ubuntu:14.04

RUN apt-get -y update
RUN apt-get install -y python-dev python-pip

COPY . /var/www/app

RUN pip install -r /var/www/app/requirements.py

CMD python /var/www/app/app.py