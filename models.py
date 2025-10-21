from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    time = db.Column(db.String(5), nullable=False)  # Format: "HH:MM"
    monday = db.Column(db.Boolean, default=False)
    tuesday = db.Column(db.Boolean, default=False)
    wednesday = db.Column(db.Boolean, default=False)
    thursday = db.Column(db.Boolean, default=False)
    friday = db.Column(db.Boolean, default=False)
    saturday = db.Column(db.Boolean, default=False)
    sunday = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'time': self.time,
            'days': [
                i for i, day in enumerate([
                    self.monday, self.tuesday, self.wednesday,
                    self.thursday, self.friday, self.saturday, self.sunday
                ]) if day
            ],
            'next_run': self.next_run_time()
        }
    
    def next_run_time(self):
        """Calculate the next time this schedule will run"""
        from datetime import datetime, timedelta
        now = datetime.now()
        hour, minute = map(int, self.time.split(':'))
        today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        days = [
            self.monday, self.tuesday, self.wednesday,
            self.thursday, self.friday, self.saturday, self.sunday
        ]
        
        # If we haven't missed today's time and today is a scheduled day
        if today > now and days[now.weekday()]:
            return today.isoformat()
            
        # Find the next scheduled day
        for i in range(1, 8):
            next_day = (now.weekday() + i) % 7
            if days[next_day]:
                return (today + timedelta(days=i)).isoformat()
        
        return None