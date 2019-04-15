import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'abcdef'
    ITEMS_PER_PAGE = 10
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ELASTICSEARCH_URL = 'http://localhost:9200'
    UPLOADED_PHOTOS_URL = os.environ.get('UPLOADED_PHOTOS_URL') or \
        'http://127.0.0.1:5000/static/img/'
    UPLOADED_PHOTOS_DEST = os.environ.get('UPLOADED_PHOTOS_DEST') or \
        'app/static/img'