# pg-video-convertor-api

Install the below libraries before running the Flask App:

ffmpeg - https://ffmpeg.org/download.html

wkhtmltopdf - https://wkhtmltopdf.org/downloads.html

libimage-exiftool-perl - https://exiftool.org/install.html

RabbitMQ - https://www.rabbitmq.com/download.html

# Project Setup:

git clone https://github.com/saravanaselvan/pg-video-convertor-api.git

cd pg-video-convertor-api

mkdir private

mkdir private/input_videos

mkdir private/output_files

touch private/celery.log

# Configuration files:

Create .env and config.py in the project root directory as below - 

# .env

export DATABASE_URL="mysql+pymysql://[USERNAME]:[PASSWORD]@[HOST]/[DATABASE]"

export UPLOAD_FOLDER = 'private/input_videos'

export OUTPUT_FOLDER = 'private/output_files'

export MODEL_NAME = '0'


# config.py

JWT_SECRET_KEY = '[RANDOM KEY]'

SQLALCHEMY_TRACK_MODIFICATIONS = False

PROPAGATE_EXCEPTIONS = True

JSON_SORT_KEYS = False

BROKER_URL = "amqp://localhost/"

CELERY_RESULT_BACKEND = "db+mysql+pymysql://[USERNAME]:[PASSWORD]@[HOST]/[DATABASE]"


# PIP Install Requirements:

python3 -m venv pg-venv

. pg-venv/bin/activate

python3 -m pip install -r requirements.txt

# Background Task:

sudo rabbitmq-server

celery -A app.celery  worker -f ~/private/celery.log --loglevel=info

# Run the app in port 8000:
python3 app.py
