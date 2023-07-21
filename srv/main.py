import configparser
import memcache
import socket

import openweather

def carbon_pack(prefix, lines):
    return ('\n'.join([prefix + '.' + s for s in lines]) + '\n').encode()

def main():
    conf = configparser.ConfigParser()
    conf.read('config.ini')

    ap = openweather.AirPollutionCurrent(
        conf['openweather']['appid'],
        conf['DEFAULT']['latitude'],
        conf['DEFAULT']['longitude']
    )
    ap.update()

    mc = memcache.Client(['{}:{}'.format(
        conf['memcache']['host'],
        conf['memcache']['port']
    )], debug=0)

    mc.set(conf['memcache']['prefix'] + '.openweather.current.airquality',
           ap.to_json())

    mc.disconnect_all()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((conf['carbon']['host'], int(conf['carbon']['port'])))
    sock.sendall(carbon_pack(conf['carbon']['prefix'] + '.openweather.airquality',
                             ap.to_carbon_text()))
    sock.close()

if __name__ == '__main__':
    main()
