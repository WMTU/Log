#!flask/bin/python
from log import app

if __name__ == '__main__':
  app.run(host = '10.0.1.10', debug = True)
