#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Calculates the darkest spot at <date> for a zenith angle below 10 degrees
(altitude of 80 degrees).
Use YYYY-MM-DD hh:mm format for date and time.


Usage:
    find_dark_spot.py [<date> <timeutc>] [options]

Options:
    --max-zenith=<degrees>    maximal zenith for the dark spot [default: 10]
    --plot                    show the selected position, does not work on gui
'''
from __future__ import division, print_function
from docopt import docopt
args = docopt(__doc__)
min_altitude = 90 - int(args['--max-zenith'])
max_zenith = int(args['--max-zenith'])

import pandas as pd
import numpy as np
from numpy import sin, cos, tan, arctan2, arcsin, pi, arccos
import ephem
from progressbar import ProgressBar
from datetime import datetime
from blessings import Terminal
term = Terminal()


def enter_datetime():
    print('\nPlease enter date and time for the ratescan')
    print(term.red('This is the real date, be aware for times after 0:00'))
    date = raw_input('Date (YYYY-MM-DD): ')
    time = raw_input('Time UTC: (hh:mm): ')
    return date, time

if args['<date>']:
    date = args['<date>']
    time = args['<timeutc>']
else:
    date, time = enter_datetime()

valid = False
while not valid:
    try:
        date = datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M')
        valid = True
    except ValueError:
        print('Could not parse date/time, please use the given notation\n')
        date, time = enter_datetime()


lapalma = ephem.Observer()
lapalma.lon = '-17:53:05'
lapalma.lat = '28:45:15'
lapalma.elevation = 2200
lapalma.date = date
lapalma.epoch = ephem.J2000

obs_long = np.deg2rad(-17 + 53/60 + 5/3600)
obs_lat = np.deg2rad(28 + 45/60 + 15/3600)


def equatorial2horizontal(ra, dec):
    ''' transforms from right ascension, declination to azimuth, altitude '''

    h = lapalma.sidereal_time() - ra
    alt = arcsin(sin(obs_lat) * sin(dec) + cos(obs_lat) * cos(dec) * cos(h))
    az = arctan2(sin(h), cos(h) * sin(obs_lat) - tan(dec)*cos(obs_lat))

    az = np.mod(az + pi, 2*pi)

    return az, alt


def angular_distance(ra1, dec1, ra2, dec2):
    ''' calculate angular distance between observer and objects '''
    term1 = sin(dec1) * sin(dec2)
    term2 = cos(dec1) * cos(dec2) * cos(ra1 - ra2)
    return arccos(term1 + term2)


def get_stars_in_fov(az, alt, stars, fov=4.6):
    '''
    returns all the stars which are in FACTs field of view pointing
    for given coords az, alt
    '''
    ra, dec = lapalma.radec_of(az, alt)
    dist = angular_distance(ra, dec, stars.ra, stars.dec)
    mask = dist <= np.deg2rad(fov/2)
    return stars.loc[mask]


def light_in_fov(az, alt, stars):
    ''' returns the total star light in the fov at azimuth az, altitude alt '''
    infov = get_stars_in_fov(az, alt, stars)
    light = infov.Vmag.apply(lambda x: 10**(-x/2.5)).sum()
    return light


stars = pd.read_csv('hipparcos_catalogue.csv')
stars.columns = 'index', 'ra', 'dec', 'HIP', 'Vmag'
stars.ra = stars.ra.apply(np.deg2rad)
stars.dec = stars.dec.apply(np.deg2rad)

sol_objects = [
    ephem.Mercury(),
    ephem.Venus(),
    ephem.Moon(),
    ephem.Mars(),
    ephem.Jupiter(),
    ephem.Saturn(),
    ephem.Uranus(),
    ephem.Neptune(),
]

for sol_object in sol_objects:
    sol_object.compute(lapalma.date)
    data = {
        'ra': float(sol_object.a_ra),
        'dec': float(sol_object.a_dec),
        'Vmag': float(sol_object.mag),
        'HIP': None,
    }
    stars = stars.append(data, ignore_index=True)


stars['azimuth'], stars['altitude'] = equatorial2horizontal(stars.ra, stars.dec)
stars = stars.query('altitude > {}'.format(np.deg2rad(min_altitude - 5)))
stars = stars.query('Vmag < 9')

azs = np.deg2rad(np.linspace(0, 360, 91))
alts = np.deg2rad(np.arange(min_altitude, 91, 0.5))
light = []
coords = []

prog = ProgressBar(maxval=len(azs) * len(alts)).start()
for i, az in enumerate(azs):
    for j, alt in enumerate(alts):
        coords.append((az, alt))
        light.append(light_in_fov(az, alt, stars))
        prog.update(i*len(alts) + j)

light = np.array(light)
coords = np.array(coords)
azs = coords[:, 0]
alts = coords[:, 1]

min_index = np.argmin(light)
best_az = azs[min_index]
best_alt = alts[min_index]

ra, dec = lapalma.radec_of(best_az, best_alt)

print(u'best ratescan position:')
print(u'RA: {:1.3f} h'.format(np.rad2deg(ra) * 24/360))
print(u'DEC: {:1.3f}°'.format(np.rad2deg(dec)))
print(u'Az: {:1.3f}°'.format(np.rad2deg(best_az)))
print(u'Alt: {:1.3f}°'.format(np.rad2deg(best_alt)))

if args['--plot']:
    # plot the skymap
    from mpl_toolkits.basemap import Basemap
    import matplotlib.pyplot as plt

    m = Basemap(
        resolution='l',
        projection='stere',
        lat_0=90,
        lon_0=0,
        llcrnrlon=135,
        llcrnrlat=90 - 1.5 * max_zenith,
        urcrnrlon=315,
        urcrnrlat=90 - 1.5 * max_zenith,
    )
    m.drawmapboundary(fill_color='black')
    m.plot(
        np.linspace(0, 360, 100),
        np.ones(100) * min_altitude,
        latlon=True,
        color='blue',
        alpha=0.6,
        )
    m.scatter(
        np.rad2deg(best_az),
        np.rad2deg(best_alt),
        latlon=True,
        lw=0,
        color='red',
    )
    m.scatter(
        np.rad2deg(stars.azimuth.values),
        np.rad2deg(stars.altitude.values),
        c=stars.Vmag,
        latlon=True,
        lw=0,
        cmap='gray_r',
        vmin=-12,
        s=0.3 * (-stars.Vmag + stars.Vmag.max())**2 + 1,
    )
    m.tissot(
        np.rad2deg(best_az),
        np.rad2deg(best_alt),
        2.25, 50, facecolor='none', edgecolor='red',
    )
    plt.colorbar(label='Visual Magnitude')
    plt.show()
