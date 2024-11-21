import os
import csv

from flask_session import Session
from datetime import timedelta
from YoHo import create_app

import sqlite3

def init_db(app):
    with app.app_context():
        db = sqlite3.connect('tickets.db')
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT,
                name TEXT,
                total_tickets INTEGER,
                zone TEXT,
                allocated_tickets INTEGER DEFAULT 0,
                source TEXT
            )
        ''')
        db.commit()
        db.close()

app = create_app()
init_db(app)
app.secret_key = 'RochesterIsChoral_gg5692_now'

#app.secret_key = os.getenv('SECRET_KEY', default='BAD_SECRET_KEY')

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)

#Need this because the cookie doesnt work in .dev server names - can take next two lines out in live (should do for security)
app.config['SESSION_COOKIE_SAMESITE'] ='None'
app.config['SESSION_COOKIE_SECURE'] = True

Session(app)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
