from app.extensions import db

class SeattleNeighbourhoods(db.Model):
    __tablename__ = 'SeattleNeighbourhoods'

    id = db.Column(db.Integer, primary_key=True)
    neighbourhood = db.Column(db.String(255), nullable=False)
    neighbourhood_sub = db.Column(db.String(255), nullable=True)

    interests = db.relationship('CustomerNeighbourhoodInterest', back_populates='neighbourhood')

    def __repr__(self):
        return (f"<SeattleNeighbourhoods(neighbourhood={self.neighbourhood}, neighbourhood_sub={self.neighbourhood_sub}")


