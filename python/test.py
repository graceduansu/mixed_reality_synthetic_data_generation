from pylab import *
#set environment variable NUMBA_DISABLE_JIT = 1 before importing sunposition to disable jit if it negatively impacts performance
# e.g. import os; os.environ['NUMBA_DISABLE_JIT'] = 1
from sunposition import sunpos
from datetime import datetime

#evaluate on a 2 degree grid
lon  = linspace(-180,180,181)
lat = linspace(-90,90,91)
LON, LAT = meshgrid(lon,lat)
#at the current time
now = datetime.utcnow()
az,zen = sunpos(now,LAT,LON,0)[:2] #discard RA, dec, H
#convert zenith to elevation
elev = 90 - zen
#convert azimuth to vectors
u, v = cos((90-az)*pi/180), sin((90-az)*pi/180)
#plot
figure()
imshow(elev,cmap=cm.CMRmap,origin='lower',vmin=-90,vmax=90,extent=(-180,180,-90,90))
s = slice(5,-1,5) # equivalent to 5:-1:5
quiver(lon[s],lat[s],u[s,s],v[s,s])
contour(lon,lat,elev,[0])
cb = colorbar()
cb.set_label('Elevation Angle (deg)')
gca().set_aspect('equal')
xticks(arange(-180,181,45)); yticks(arange(-90,91,45))
