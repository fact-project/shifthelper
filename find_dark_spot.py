#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Calculates the darkest spot at <date> for a zenith angle below 10 degrees
(altitude of 80 degrees)

Please give the date and time like this: 2015-07-11 1:00

Usage:
    find_dark_spot.py <date> <timeutc> [options]

Options:
    --max-zenith=<degrees>    maximal zenith for the dark spot [default: 10]
    --plot                    show the selected position, does not work on gui
'''
from __future__ import division, print_function
from docopt import docopt
args = docopt(__doc__)

import pandas as pd
import numpy as np
from numpy import sin, cos, tan, arctan2, arcsin, pi, arccos
import ephem
from progressbar import ProgressBar

lapalma = ephem.Observer()
lapalma.lon = '-17:53:05'
lapalma.lat = '28:45:15'
lapalma.elevation = 2200
lapalma.date = args['<date>'] + ' ' + args['<timeutc>']
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

def get_stars_in_fov(az, alt, stars, fov=4.5):
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

stars['azimuth'], stars['altitude'] = equatorial2horizontal(stars.ra, stars.dec)
stars = stars.query('altitude > {}'.format(np.deg2rad(70)))
stars = stars.query('Vmag < 9')

azs = np.deg2rad(np.linspace(0, 360, 91))
alts = np.deg2rad(np.arange(90 - int(args['--max-zenith']), 91, 0.5))
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
        width=0.3e7,
        height=0.3e7,
    )
    m.drawmapboundary(fill_color='black')
    m.drawparallels([0, 80], color='gray', dashes=[5,5])
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
        c=-stars.Vmag,
        latlon=True,
        lw=0,
        cmap='gray',
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
