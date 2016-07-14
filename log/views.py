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
    if artist.startswith('The '):
      return artist[4:]
    if artist.startswith('A '):
      return artist[2:]
    if artist.startswith('An '):
      return artist[3:]
    return artist


  def get(self):
    timezone_local = timezone("America/Detroit")

    # Construct a datetime object for today's date at midnight Eastern time
    date_today = date.today()
    datetime_today_midnight_local = datetime.combine(date_today, time(0, 0, 0))
    datetime_today_midnight_local_str = timezone_local.localize(datetime_today_midnight_local).isoformat()

    # Construct a datetime object for today's date at 23:59:59 Eastern time
    datetime_today_23_59_59_local = datetime_today_midnight_local + timedelta(seconds = 59, minutes = 59, hours = 23)
    datetime_today_23_59_59_local_str = timezone_local.localize(datetime_today_23_59_59_local).isoformat()

    # Define a parser for the GET request arguments (all optional)
    #   n:      number of results to return
    #   start:  a datetime beginning at the value of which results will be returned
    #   end:    a datetime ending at the value of which results will be returned
    #   id:     an ID after which results will be returned
    #   delay:  whether or not the results returned should reflect the 30-second broadcast delay
    parser = reqparse.RequestParser()
    parser.add_argument('n', type = int, default = 4294967295, location = 'args')
    parser.add_argument('start', type = str, default = datetime_today_midnight_local_str, location = 'args')
    parser.add_argument('end', type = str, default = datetime_today_23_59_59_local_str, location = 'args')
    parser.add_argument('id', type = int, default = -1, location = 'args')
    parser.add_argument('delay', type = bool, default = False, location = 'args')
    parser.add_argument('desc', type = bool, default = False, location = 'args')

    # Parse GET request arguments
    args = parser.parse_args()
    
    # Convert start and end to datetime
    start_no_colon = args['start'].replace(':','')
    start_conformed_timestamp = start_no_colon[:-5].replace('-','') + start_no_colon[-5:]
    args['start'] = datetime.strptime(start_conformed_timestamp, "%Y%m%dT%H%M%S%z" )
    end_no_colon = args['end'].replace(':','')
    end_conformed_timestamp = end_no_colon[:-5].replace('-','') + end_no_colon[-5:]
    args['end'] = datetime.strptime(end_conformed_timestamp, "%Y%m%dT%H%M%S%z" )

    # Convert start and end to Eastern time
    args['start'] = args['start'].astimezone(timezone_local)
    args['end'] = args['end'].astimezone(timezone_local)

    # If delay argument is True, subtract 30 seconds from start and end
    if (args['delay']):
      args['start'] = args['start'] - timedelta(seconds = 30)
      args['end'] = args['end'] - timedelta(seconds = 30)

    # Query the database using the id and timestamp arguments
    songs = Song.query\
                .filter(Song.id > args['id'])\
                .filter(Song.ts >= args['start'])\
                .filter(Song.ts <= args['end'])

    # Filter the results depending on the presence of the desc argument
    if (args['desc']):
      songs = songs.order_by(Song.id.desc())

    # Limit the number of results to n
    songs = songs.limit(args['n'])

    # Return results
    return { 'songs': [s.serialize for s in songs] }


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
    return { 'song': marshal(new_song, song_fields) }


class SongAPI(Resource):
  def get(self, id):
    song = Song.query.filter_by(id = id).first_or_404()
    return { 'song': marshal(song, song_fields) }


class ChartsAPI(Resource):
  def get(self):
    # TODO
    pass


api.add_resource(SongListAPI, '/log/api/v1.0/songs', endpoint = 'songs')
api.add_resource(SongAPI, '/log/api/v1.0/song/<int:id>', endpoint = 'song')
api.add_resource(ChartsAPI, '/log/api/v1.0/charts', endpoint = 'charts')
