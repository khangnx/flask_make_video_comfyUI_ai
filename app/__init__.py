
rom flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['VIDEO_FOLDER'] = 'app/static/videos'
    return app
