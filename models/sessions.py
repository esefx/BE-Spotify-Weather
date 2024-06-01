from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Session(db.Model):
    __tablename__ = 'sessions'
    user_id = db.Column(db.String, primary_key=True)
    access_token = db.Column(db.String)
    refresh_token = db.Column(db.String)
    expires_at = db.Column(db.Float)