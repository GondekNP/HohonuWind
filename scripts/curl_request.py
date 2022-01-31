# import requests
import urllib.request as rq
import datetime
import math
import xarray as xr
import os
import wget

# download the most recent GFS predictions via NOMAD, optionally subset to 
# specific latitude/longitude window
call_time = datetime.datetime.now()
nomad_par = {
    'date_format' : call_time.strftime('%Y%m%d'),
    'lat_min' : -90,
    'lat_max' : 90,
    'lon_min' : 0,
    'lon_max' : 360,
    'hour_format' : str(math.floor(call_time.hour / 6) * 6).zfill(2)
}

# surface level data from https://nomads.ncep.noaa.gov/
nomad_call = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?" +\
    "file=gfs.t{hour_format}z.pgrb2.0p25.anl&lev_surface=on&all_var=on&subregion=" +\
    "&leftlon={lon_min}&rightlon={lon_max}" +\
    "&toplat={lat_max}&bottomlat={lat_min}" +\
    "&dir=%2Fgfs.{date_format}%2F{hour_format}%2Fatmos"

nomad_call = nomad_call.format(**nomad_par)

if not os.path.exists('tmp/'):
    os.mkdir('tmp/')

# after many attempts to do so, not possible to read cfgrib directly to memory
# without first saving to disk. As a result we need to download the grib file
# and rename it w/ .grib extension to properly ingest it

wget.download(nomad_call, out = 'tmp/temp_df.grib')
df = xr.open_dataset('tmp/temp_df.grib', engine='cfgrib')
