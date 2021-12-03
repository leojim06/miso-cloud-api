import os
from typing import Dict
from flask import Flask

def create_app(config_dict: Dict = {}) -> Flask:
    app = Flask("main")

    DATABASE_URI = os.environ.get('DATABASE_URI')
    BUCKET_NAME = os.environ.get('BUCKET_NAME')
    SQS_URL = os.environ.get('SQS_URL')
    SECRET = os.environ.get('SECRET')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['JWT_SECRET_KEY'] = SECRET
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['BUCKET_NAME'] = BUCKET_NAME
    app.config['SQS_URL'] = SQS_URL
    app.config['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
    app.config['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY

    return app