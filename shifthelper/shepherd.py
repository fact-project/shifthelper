import pytz
import requests
import dateutil
import dateutil.parser
from datetime import datetime
from twilio.rest import RestClient as Client
from .tools import config
import time

c = config

url = 'https://ihp-pc41.ethz.ch/time'
# -> {  "time": "Fri, 07 Apr 2017 10:37:15 GMT" }

TIMEOUT = 10 * 60  # timeout in seconds
hangup_twiml = '''<Response><Hangup/></Response>'''
hangup_url = build_url(echo_url, {'Twiml': hangup_twiml})


def check_server_time():
    try:
        server_time = dateutil.parser.parse(
            requests.get(url).json()['time']
        )
        delta = datetime.now(pytz.utc) - server_time
        if delta.total_seconds() > TIMEOUT:
            raise Exception('servertime too old')
    except:
        Client(
            c['twilio']['sid'],
            c['twilio']['auth_token']
            ).calls.create(
                to=c['developer']['phone_number'],
                from_=c['twilio']['number'],
                url=hangup_url,
                timeout=20,
        )

if __name__ == "__main__":
    while True:
        check_server_time()
        time.sleep(60)
