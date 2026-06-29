# Add to the bottom of database.py
from models import Base   # imports all models including User
from database import engine

Base.metadata.create_all(bind=engine)   # creates all tables including users