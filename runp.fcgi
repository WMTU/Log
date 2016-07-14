#!flask/bin/python
from flipflop import WSGIServer
from log import app

if __name__ == '__main__':
    WSGIServer(app).run()
