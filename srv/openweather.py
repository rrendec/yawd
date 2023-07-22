import requests
import json

import gas
import epaaqi

BASE_URL = 'https://api.openweathermap.org'

class BaseApi:
    def __init__(self, appid):
        self.appid = appid

    def get_url_query(self):
        return 'appid=' + self.appid

    def to_json(self):
        return json.dumps(self.data)

class LocalizedApi(BaseApi):
    def __init__(self, appid, lat, lon):
        super().__init__(appid)
        self.lat = lat
        self.lon = lon

    def get_url_query(self):
        return '&'.join((
            'lat={}&lon={}'.format(self.lat, self.lon),
            super().get_url_query()
        ))

class Weather(LocalizedApi):
    def get_url_query(self):
        return '&'.join(('units=metric', super().get_url_query()))

    @staticmethod
    def normalize(data, altitude_m):
        data = data.copy()

        data['main']['pressure'] *= 100

        if 'sea_level' in data['main']:
            data['main']['sea_level'] *= 100
        else:
            data['main']['sea_level'] = data['main']['pressure']

        if 'grnd_level' in data['main']:
            data['main']['grnd_level'] *= 100
        else:
            data['main']['grnd_level'] = round(gas.air_pressure(
                data['main']['sea_level'],
                data['main']['temp'],
                altitude_m
            ) / 100) * 100

        return data

class WeatherCurrent(Weather):
    def update(self, altitude_m=0):
        url = BASE_URL + '/data/2.5/weather?' + self.get_url_query()
        res = requests.get(url)
        res.raise_for_status()
        self.data = Weather.normalize(json.loads(res.content), altitude_m)
        del self.data['coord']

    def to_carbon_text(self):
        return ['{} {} {}'.format(unit, value, self.data['dt']) for unit, value in [
            ('id', self.data['weather'][0]['id']),
        ] + list(self.data['main'].items()) + [
            ('visibility', self.data['visibility']),
            ('wind.speed', self.data['wind']['speed']),
            ('wind.deg', self.data['wind']['deg']),
        ]]

class AirPollution(LocalizedApi):
    components = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
    gas_aqi_scale = {'o3': 1000, 'pm2_5': 1, 'pm10': 1, 'co': 1000, 'so2': 1, 'no2': 1}

    @staticmethod
    def normalize(data, temp_c, pres_pa):
        # All our input data (from the OpenWeather API) uses ug/m^3, and
        # gas.to_ppm() expects mg/m^3, so we get back ppb instead of ppm.
        ppb = {k: gas.to_ppm(k, v, temp_c, pres_pa)
               for k, v in data['components'].items() if k in gas.molecular_weight}
        aqi = {k: v / AirPollution.gas_aqi_scale[k] if k.startswith('pm')
               else gas.to_ppm(k, v / AirPollution.gas_aqi_scale[k], temp_c, pres_pa)
               for k, v in data['components'].items() if k in AirPollution.gas_aqi_scale}
        aqi = {
            'o3-8': epaaqi.aqi('o3-8', aqi['o3']),
            'o3-1': epaaqi.aqi('o3-1', aqi['o3']),
        } | {k: epaaqi.aqi(k, v) for k, v in aqi.items() if k != 'o3'}

        return {
            'aql': data['main']['aqi'],
            'aqi': max([v for v in aqi.values() if v is not None]),
            'cmass': data['components'],
            'cvol': ppb,
            'caqi': aqi,
            'dt': data['dt']
        }

class AirPollutionCurrent(AirPollution):

    def update(self, temp_c=gas.STD_TEMP_C, pres_pa=gas.STD_PRES_PA):
        url = BASE_URL + '/data/2.5/air_pollution?' + self.get_url_query()
        res = requests.get(url)
        res.raise_for_status()
        self.data = AirPollution.normalize(json.loads(res.content)['list'][0],
                                           temp_c, pres_pa)

    def to_carbon_text(self):
        return [
            '{} {} {}'.format(k, self.data[k], self.data['dt']) for k in ['aql', 'aqi']
        ] + [
            'cmass.{} {} {}'.format(k, v, self.data['dt']) for k, v in self.data['cmass'].items()
        ] + [
            'cvol.{} {} {}'.format(k, v, self.data['dt']) for k, v in self.data['cvol'].items()
        ] + [
            'caqi.{} {} {}'.format(k, v, self.data['dt']) for k, v in self.data['caqi'].items()
            if v is not None
        ]
