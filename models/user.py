from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    access_token = db.Column(db.String)
    refresh_token = db.Column(db.String)
    expires_at = db.Column(db.String)
    user_id = db.Column(db.String)
    
    def json(self):
        return {
            "id": self.id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id
        }