from log import app
from flask_sqlalchemy import SQLAlchemy

# Create database object
db = SQLAlchemy(app)

# Bind the declarative base to an engine
db.Model.metadata.reflect(db.engine, only = ['djlogs'])

# Define Song class for existing djlogs table
class Song(db.Model):
  __table__ = db.Model.metadata.tables['djlogs']
