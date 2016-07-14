from log import app
from flask_sqlalchemy import SQLAlchemy

# Create database object
db = SQLAlchemy(app)

# Bind the declarative base to an engine
db.Model.metadata.reflect(db.engine, only = ['djlogs'])

def dump_datetime(value):
  # Deserialize datetime object into string form for JSON processing.
  if value is None:
    return None
  return value.strftime("%Y-%m-%d") + 'T' + value.strftime("%H:%M:%S")

# Define Song class for existing djlogs table
class Song(db.Model):
  __table__ = db.Model.metadata.tables['djlogs']

  @property
  def serialize(self):
    # Return object data in easily serializeable format
    return {
      'id'               : self.id,
      'cd_number'        : self.cd_number,
      'song_name'        : self.song_name,
      'artist'           : self.artist,
      'genre'            : self.genre,
      'album'            : self.album,
      'score'            : self.score,
      'location'         : self.location,
      'truncated_artist' : self.truncated_artist,
      'ts'               : dump_datetime(self.ts)
    }
