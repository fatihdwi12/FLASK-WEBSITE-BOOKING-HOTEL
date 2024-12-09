import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hotel_booking.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)  # Untuk session Flask
