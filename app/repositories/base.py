from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, instance):
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
