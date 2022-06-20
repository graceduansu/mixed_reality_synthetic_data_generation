#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import sys

if __name__ == '__main__':
    # Required arguments
    parser.add_argument('--turbidity',type=float, )

    # optional arguments (default values listed in car_road_template.xml)
    parser.add_argument('--turbidity',type=float)
    parser.add_argument('-lat,--latitude',dest='lat',type=float)
    parser.add_argument('-lon,--longitude',dest='lon',type=float)
    parser.add_argument('--timezone',type=float)
    parser.add_argument('--year',type=int)
    parser.add_argument('--month',type=int)
    parser.add_argument('--day',type=int)
    parser.add_argument('--hour',type=float)
    parser.add_argument('--minute',type=float)
    parser.add_argument('--cameraToWorldMatrix',type=string)
    parser.add_argument('--fov',type=float)
    parser.add_argument('--sampleCount',type=int)
    parser.add_argument('--width',type=int)
    parser.add_argument('--height',type=int)
    parser.add_argument('--roadScale',type=float)

    
    args = parser.parse_args()
   
def main(args):
    az, zen, ra, dec, h = sunpos(args.t, args.lat, args.lon, args.elev, args.temp, args.p, args.dt, args.rad)
    

if __name__ == '__main__':
    main(args)