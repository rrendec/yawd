import configparser
import memcache
import socket

import openweather
import waqi

def carbon_pack(prefix, lines):
    return ('\n'.join([prefix + '.' + s for s in lines]) + '\n').encode()

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

    mc.disconnect_all()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((conf['carbon']['host'], int(conf['carbon']['port'])))
    sock.sendall(carbon_pack(conf['carbon']['prefix'], ds_ow_w.to_carbon_text()))
    sock.sendall(carbon_pack(conf['carbon']['prefix'], ds_ow_ap.to_carbon_text()))
    for ds in ds_waqi:
        sock.sendall(carbon_pack(conf['carbon']['prefix'], ds.to_carbon_text()))
    sock.close()

if __name__ == '__main__':
    main()
