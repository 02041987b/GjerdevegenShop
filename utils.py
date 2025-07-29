import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_image(file):
    if file.content_length > current_app.config['MAX_FILE_SIZE']:
        raise ValueError("File size exceeds 2MB limit")
    if not allowed_file(file.filename):
        raise ValueError("Invalid file extension")
    return secure_filename(file.filename)