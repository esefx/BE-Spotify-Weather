from app import db
import datetime

class TemporaryStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def cleanup():
        now = datetime.datetime.utcnow()
        TemporaryStorage.query.filter(TemporaryStorage.expires_at < now).delete()
        db.session.commit()
