from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Run(db.Model):
    __tablename__ = "runs"

    id = db.Column(db.Integer, primary_key=True)

    # Performance Metrics
    max_speed = db.Column(db.Float, nullable=False)
    zero_to_hundred = db.Column(db.Float, nullable=True)
    distance = db.Column(db.Float, nullable=False)

    # GPS Route (list of [lat, lon])
    route_data = db.Column(db.Text, nullable=True)

    # Telemetry (list of speed values)
    telemetry_data = db.Column(db.Text, nullable=True)

    # Lap detection result (list of lap distances)
    lap_data = db.Column(db.Text, nullable=True)

    # AI analysis result
    analysis = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ==========================
    # SERIALIZATION METHOD
    # ==========================
    def to_dict(self):
        return {
            "id": self.id,
            "max_speed": self.max_speed,
            "zero_to_hundred": self.zero_to_hundred,
            "distance": self.distance,
            "route_data": json.loads(self.route_data) if self.route_data else [],
            "telemetry_data": json.loads(self.telemetry_data) if self.telemetry_data else [],
            "lap_data": json.loads(self.lap_data) if self.lap_data else [],
            "analysis": self.analysis,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }