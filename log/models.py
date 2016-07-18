from log import app
from flask_sqlalchemy import SQLAlchemy

# Create database object
db = SQLAlchemy(app)

# Bind the declarative base to an engine
db.Model.metadata.reflect(db.engine, only = ['djlogs', 'discrepency_logs'])

# Define Song class for existing djlogs table
class Song(db.Model):
  __table__ = db.Model.metadata.tables['djlogs']

# Define Discrepancy class for existing discrepancy_logs table
class Discrepancy(db.Model):
  __table__ = db.Model.metadata.tables['discrepency_logs']

