import requests
import json
import datetime

import util

BASE_URL = 'https://api.waqi.info'

class BaseApi:
    def __init__(self, token):
        self.token = token

    def get_url_query(self):
        return 'token=' + self.token

    def to_json(self):
        return json.dumps(self.data)

    @staticmethod
    def request(url):
        res = requests.get(url)
        res.raise_for_status()
        data = json.loads(res.content)
        assert data['status'] == 'ok'
        return data['data']

class Feed(BaseApi):
    weather_map = {
        't': ('temperature', 1),
        'h': ('humidity', 1),
        'p': ('pressure', 100),
    }
    aqi_comp_map = {
        'co': 'co',
        'no': 'no',
        'no2': 'no2',
        'o3': 'o3',
        'so2': 'so2',
        'pm25': 'pm2_5',
        'pm10': 'pm10',
        'nh3': 'nh3',
    }

    def update(self):
        data = BaseApi.request(self.url + '?' + self.get_url_query())
        self.data = Feed.normalize(data)

    @staticmethod
    def normalize(data):
        ret = {k: data[k] for k in ['idx', 'attributions', 'city']}
        ret['weather'] = {
            v[0]: data['iaqi'][k]['v'] * v[1]
            for k, v in Feed.weather_map.items()
            if k in data['iaqi']
        }
        ret['airquality'] = {
            'aqi': {'epa': data['aqi']},
            'caqi': {'epa': {
                v: data['iaqi'][k]['v']
                for k, v in Feed.aqi_comp_map.items()
                if k in data['iaqi']
            }},
        }
        if 'forecast' in data:
            ret['forecast'] = {
                v: data['forecast']['daily'][k]
                for k, v in Feed.aqi_comp_map.items()
                if k in data['forecast']['daily']
            }
        dt = datetime.datetime.strptime(data['time']['s'], '%Y-%m-%d %H:%M:%S')
        ret['dt'] = int(dt.timestamp())

        return ret

    def to_carbon_text(self):
        return [
            '{}.weather.{} {} {}'.format(self.prefix, k, v, self.data['dt'])
            for k, v in self.data['weather'].items()
        ] + [
            '{}.airquality.{} {} {}'.format(self.prefix, k, v, self.data['dt'])
            for k, v in util.flatten(self.data['airquality']).items()
        ]

class CityFeed(Feed):
    def __init__(self, token, city, prefix='waqi.main'):
        super().__init__(token)
        # This is documented. We can user either '<name>' or '@<id>' to
        # identify an official station. The corresponding map URL is:
        # https://aqicn.org/city/<name>
        self.url = BASE_URL + '/feed/{}/'.format(city)
        self.prefix = prefix

class StationFeed(Feed):
    def __init__(self, token, station_id, prefix=None):
        super().__init__(token)
        # This is not documented. We can use either 'A<id>' or '@-<id>' to
        # identify an unofficial station. The corresponding map URL is:
        # https://aqicn.org/station/@<id>
        self.url = BASE_URL + '/feed/A{}/'.format(station_id)
        self.prefix = prefix or 'waqi.s' + str(station_id)
