from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):  # Pastikan UserMixin ada di sini
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)  # Menambahkan kolom is_active
    
    # Relasi dengan Booking
    bookings = db.relationship('Booking', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        return self.role == 'admin'

# Model Hotel
class Hotel(db.Model):
    __tablename__ = 'hotel'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price_per_night = db.Column(db.Integer, nullable=False)
    images = db.Column(db.String(500), nullable=True)  # Kolom images yang baru ditambahkan
    available_rooms = db.Column(db.Integer, nullable=False, default=0)
    
    # Relasi dengan Booking
    bookings = db.relationship('Booking', back_populates='hotel')
    
    def __repr__(self):
        return f'<Hotel {self.name}>'

# Model Booking
class Booking(db.Model):
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)  # Perbaiki nama tabel hotel
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Perbaiki nama tabel user
    check_in_date = db.Column(db.DateTime, nullable=False)
    check_out_date = db.Column(db.DateTime, nullable=False)
    
    # Relasi ke Hotel dan User
    hotel = db.relationship('Hotel', back_populates='bookings')
    user = db.relationship('User', back_populates='bookings')

    def __repr__(self):
        return f"<Booking {self.id} for {self.user_id} at {self.hotel_id}>"
