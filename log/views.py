from log import app
from flask import request, jsonify
from flask_restful import Api, fields, Resource, reqparse, marshal
from pytz import timezone, utc
from datetime import datetime, date, time, timedelta
from .models import db, Song
from threading import Timer
from .publishers import publish

api = Api(app)

song_fields = {
  'timestamp': fields.DateTime(dt_format = 'iso8601', attribute = 'ts'),
  'location': fields.String,
  'asset_id': fields.String(attribute = 'cd_number'),
  'title': fields.String(attribute = 'song_name'),
  'artist': fields.String,
  'album': fields.String,
  'genre': fields.String,
  'uri': fields.Url('song')
}


class SongListAPI(Resource):
  def truncate_artist(self, artist):
    # Remove leading 'The ', 'A ', or 'An '
    if artist.startswith('The '):
      artist = artist[4:]
    elif artist.startswith('A '):
      artist = artist[2:]
    elif artist.startswith('An '):
      artist = artist[3:]

    # Remove trailing featured artists
    sep = ' feat. '
    return artist.split(sep, 1)[0]


  def get(self):
    # Define a parser for the GET request arguments (all optional)
    #   n:      number of results to return
    #   start:  a datetime beginning at the value of which results will be returned
    #   end:    a datetime ending at the value of which results will be returned
    #   id:     an ID after which results will be returned
    #   delay:  whether or not the results returned should reflect the 30-second broadcast delay
    parser = reqparse.RequestParser()
    parser.add_argument('n', type = int, default = 500, location = 'args')
    parser.add_argument('date', type = str, default = "", location = 'args')
    parser.add_argument('id', type = int, default = -1, location = 'args')
    parser.add_argument('delay', type = bool, default = False, location = 'args')
    parser.add_argument('desc', type = bool, default = False, location = 'args')

    # Parse GET request arguments
    args = parser.parse_args()
    
    # Query the database, filtering on the id argument
    songs = Song.query.filter(Song.id > args['id'])

    # If the date argument is present, only return records from that day
    if (args['date']):
      date = datetime.strptime(args['date'], "%Y-%m-%d").date()
      songs = songs.filter(Song.ts.between(datetime.combine(date, time(0, 0, 0)),
                                           datetime.combine(date, time(23, 59, 59))))

    # If delay argument is True, only return records that are at least 30 seconds old
    if (args['delay']):
      songs = songs.filter(Song.ts < datetime.now() - timedelta(seconds = 30))

    # Filter the results depending on the presence of the desc argument
    if (args['desc']):
      songs = songs.order_by(Song.id.desc())

    # Limit the number of results to n
    songs = songs.limit(args['n'])

    # Return results
    return { 'songs': [marshal(s, song_fields) for s in songs] }, 200, {'Access-Control-Allow-Origin': '*'}


  def post(self):
    timezone_local = timezone("America/Detroit")

    # Define a parser for the POST request arguments
    #   location: section of music library from which the song came (required)
    #   asset_id: unique identifier for recording (alpha tag for CD or LP; media asset ID for WideOrbit file)
    #   title:    song title (required)
    #   artist:   song artist (required)
    #   album:    song album
    #   genre:   song genre
    parser = reqparse.RequestParser()
    parser.add_argument('location', type = str, required = True, help = 'No record location provided', location = 'json')
    parser.add_argument('asset_id', type = str, default = "", location = 'json')
    parser.add_argument('title', type = str, required = True, help = 'No song title provided', location = 'json')
    parser.add_argument('artist', type = str, required = True, help = 'No artist name provided', location = 'json')
    parser.add_argument('album', type = str, default = "", location = 'json')
    parser.add_argument('genre', type = str, default = "", location = 'json')

    # Parse POST request arguments
    args = parser.parse_args()

    # Build a new song object from the parsed arguments
    new_song = Song(cd_number         = args['asset_id'],
                    song_name         = args['title'],
                    artist            = args['artist'],
                    genre             = args['genre'],
                    album             = args['album'],
                    location          = args['location'],
                    truncated_artist  = self.truncate_artist(args['artist']),
                    ts                = datetime.now(timezone_local))

    # Add the new song to the database
    db.session.add(new_song)
    db.session.commit()
    
    # Create and start a timer to publish the new song to Icecast, TuneIn and Last.fm after 30 seconds (to account for the broadcast delay)
    timestamp_loc = timezone_local.localize(new_song.ts)
    timestamp_utc = timestamp_loc.astimezone(utc)
    t = Timer(30.0, publish, [new_song.song_name, new_song.artist, new_song.album, timestamp_utc])
    t.start()

    # Return new song
    return { 'song': marshal(new_song, song_fields) }, 202, {'Access-Control-Allow-Origin': '*'}


class SongAPI(Resource):
  def get(self, id):
    song = Song.query.filter_by(id = id).first_or_404()
    return { 'song': marshal(song, song_fields) }, 200, {'Access-Control-Allow-Origin': '*'}


class ChartsAPI(Resource):
  def get(self):
    # TODO
    pass


api.add_resource(SongListAPI, '/log/api/v1.0/songs', endpoint = 'songs')
api.add_resource(SongAPI, '/log/api/v1.0/song/<int:id>', endpoint = 'song')
api.add_resource(ChartsAPI, '/log/api/v1.0/charts', endpoint = 'charts')
