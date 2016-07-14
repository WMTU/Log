from log import app
from pylast import LastFMNetwork, md5
from requests import get

# Connect to the Last.fm network
network = LastFMNetwork(api_key       = app.config['LASTFM_API_KEY'],
                        api_secret    = app.config['LASTFM_API_SECRET'],
                        username      = app.config['LASTFM_USERNAME'],
                        password_hash = md5(app.config['LASTFM_PASSWORD']))

def publish(title, artist, album, timestamp):
  # Scrobble to Last.fm
  network.scrobble(artist=artist, title=title, timestamp=timestamp)
  
  # Setup TuneIn parameters
  params = {'partnerId':  app.config['TUNEIN_PARTNER_ID'],
            'partnerKey': app.config['TUNEIN_PARTNER_KEY'],
            'id':         app.config['TUNEIN_STATION_ID'],
            'title':      title,
            'artist':     artist}
  if (album):
    params['album'] = album
  get('http://air.radiotime.com/Playing.ashx', params = params)

  # TODO: Icecast