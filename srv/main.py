import configparser
import memcache
import socket
import datetime
import json

import openweather
import waqi
import util

def carbon_pack(prefix, lines):
    return ('\n'.join([prefix + '.' + s for s in lines]) + '\n').encode()

def aggregate(ds_ow_w, ds_ow_ap, ds_waqi):
    # This is currently based on mere observation, and specific to the data
    # sources around my area. It needs to be adapted to use a more generic
    # algorithm and/or additional configuration data.
    #   - OpenWeather air quality data is way off; do not use it
    #   - WAQI city values for temperature, humidity, pressure are good
    #     but the reporting station is too far away
    #   - WAQI city values for NO2 and O3 are supposed to be integer
    #     values, but they are not, so something is odd
    #   - WAQI station values for temperature and humidity are way off
    #   - WAQI station values for PM2.5 and PM10 seem to be accurate

    dt = int(datetime.datetime.now().timestamp())
    aqi_epa = {}
    for name in waqi.Feed.aqi_comp_map.values():
        val = [
            ds.data['airquality']['caqi']['epa'][name]
            for ds in ds_waqi
            if name in ds.data['airquality']['caqi']['epa']
        ]
        if val:
            aqi_epa[name] = round(max(val))

    return {
        'weather': {
            'temperature': ds_ow_w.data['main']['temperature'],
            'humidity': ds_ow_w.data['main']['humidity'],
            'pressure': ds_ow_w.data['main']['pressure'],
        },
        'airquality': {
            'aqi': {
                'epa': max(aqi_epa.values())
            },
            'caqi': {
                'epa': aqi_epa
            }
        },
        'dt': dt
    }

def main():
    conf = configparser.ConfigParser()
    conf.read('config.ini')

    ds_ow_w = openweather.WeatherCurrent(
        conf['openweather']['appid'],
        conf['DEFAULT']['latitude'],
        conf['DEFAULT']['longitude']
    )
    ds_ow_w.update(int(conf['DEFAULT']['altitude']))

    ds_ow_ap = openweather.AirPollutionCurrent(
        conf['openweather']['appid'],
        conf['DEFAULT']['latitude'],
        conf['DEFAULT']['longitude']
    )
    ds_ow_ap.update(ds_ow_w.data['main']['temperature'])

    ds_waqi = [waqi.CityFeed(conf['waqi']['token'], conf['waqi']['city'])]
    for token in conf['waqi']['stations'].split(','):
        station_id = int(token.strip())
        ds_waqi.append(waqi.StationFeed(conf['waqi']['token'], station_id))
    for ds in ds_waqi:
        ds.update()

    ag = aggregate(ds_ow_w, ds_ow_ap, ds_waqi)

    mc = memcache.Client(['{}:{}'.format(
        conf['memcache']['host'],
        conf['memcache']['port']
    )], debug=0)

    mc.set(conf['memcache']['prefix'] + '.openweather.current.weather',
           ds_ow_w.to_json())
    mc.set(conf['memcache']['prefix'] + '.openweather.current.airquality',
           ds_ow_ap.to_json())
    for ds in ds_waqi:
        mc.set(conf['memcache']['prefix'] + '.' + ds.prefix, ds.to_json())
    mc.set(conf['memcache']['prefix'] + '.aggregate', json.dumps(ag))

    mc.disconnect_all()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((conf['carbon']['host'], int(conf['carbon']['port'])))
    sock.sendall(carbon_pack(conf['carbon']['prefix'], ds_ow_w.to_carbon_text()))
    sock.sendall(carbon_pack(conf['carbon']['prefix'], ds_ow_ap.to_carbon_text()))
    for ds in ds_waqi:
        sock.sendall(carbon_pack(conf['carbon']['prefix'], ds.to_carbon_text()))
    sock.sendall(carbon_pack(conf['carbon']['prefix'], [
        'aggregate.{} {} {}'.format(k, v, ag['dt'])
        for k, v in util.flatten(ag).items() if k != 'dt'
    ]))
    sock.close()

if __name__ == '__main__':
    main()
