from log import app
from pylast import LastFMNetwork, md5
from requests import get

# Connect to the Last.fm network
network = LastFMNetwork(api_key       = app.config['LASTFM_API_KEY'],
                        api_secret    = app.config['LASTFM_API_SECRET'],
                        username      = app.config['LASTFM_USERNAME'],
                        password_hash = md5(app.config['LASTFM_PASSWORD']))

# Setup TuneIn parameters
ti_params = {'partnerId':  app.config['TUNEIN_PARTNER_ID'],
             'partnerKey': app.config['TUNEIN_PARTNER_KEY'],
             'id':         app.config['TUNEIN_STATION_ID']}

def publish(title, artist, album, timestamp):
  # Scrobble to Last.fm
  network.scrobble(artist=artist, title=title, timestamp=timestamp, album = album)

  # Update TuneIn metadata
  ti_params['title']   = title
  ti_params['artist']  = artist
  if (album):
    ti_params['album'] = album
  get(app.config['TUNEIN_API_URI'], params = ti_params)

  # Update Icecast metadata
  uri = app.config['ICECAST_SERVER_URI'] + "admin/metadata"
  ic_params = {'mode': 'updinfo',
               'song': artist + " | " + title}
  for m in app.config['ICECAST_MOUNTPOINTS']:
    ic_params['mount'] = m
    get(uri, params = ic_params, auth = (app.config['ICECAST_USERNAME'], app.config['ICECAST_PASSWORD']))