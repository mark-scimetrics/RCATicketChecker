import os

import shutil
from flask import Flask


def create_app():
  app = Flask(__name__)
  app.config['SESSION_COOKIE_PATH'] = "/"
  app.config['SESSION_FILE_DIR']='flask_session_files'

  
  with app.app_context():
    #Clean up the session files
    session_dir = app.config['SESSION_FILE_DIR']

    if os.path.exists(session_dir):
      shutil.rmtree(session_dir)

    os.makedirs(session_dir)  # Recreate the directory after removing it
   
    # Import parts of our core Flask app
    import views

    # Register Blueprints
    app.register_blueprint(views.appbp)

  return app
