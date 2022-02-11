import urllib.request as rq
import datetime
import math
import xarray as xr
import xarray_extras.csv as xcsv
import os
import wget

def retrieve_nomad(lat_range = (-90, 90),
                   lon_range = (0, 360),
                   out_type = 'xarray',
                   csv_path = 'temp_grib.csv',
                   temp_dir = 'tmp/'):
    '''
    Retrieves GFS predictions via NOMAD API, optionally filtering to a specific
    lat/lon window. By default, returns an xarray object - other options are 
    csv and pandas.DataFrame(). 

    Inputs:
        lat_range: (tuple) of minimum, maximum lat in degrees
        lon_range: (tuple) of minimum, maximum lon in degrees
        out_type: one of {'xrray', 'csv', 'pandas'}
        csv_path: if out_type is 'csv', path to save csv

    Output:
        An xarray object, pandas dataframe, or None (with a csv saved to the 
        csv path)

    '''

    # download the most recent GFS predictions via NOMAD, optionally subset to 
    # specific latitude/longitude window
    call_time = datetime.datetime.now()

    nomad_par = {
        'date_format' : call_time.strftime('%Y%m%d'),
        'lat_min' : lat_range[0],
        'lat_max' : lat_range[1],
        'lon_min' : lon_range[0],
        'lon_max' : lon_range[1],
        'hour_format' : str(math.floor(call_time.hour / 6) * 6).zfill(2)
    }

    # surface level data from https://nomads.ncep.noaa.gov/
    nomad_call = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?" +\
        "file=gfs.t{hour_format}z.pgrb2.0p25.anl&" +\
        "lev_surface=on&all_var=on" +\
        "&leftlon={lon_min}&rightlon={lon_max}" +\
        "&toplat={lat_max}&bottomlat={lat_min}" +\
        "&dir=%2Fgfs.{date_format}%2F{hour_format}%2Fatmos"

    nomad_call = nomad_call.format(**nomad_par)

    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    else:
        for file in os.scandir(temp_dir):
            os.remove(file.path)


    # after many attempts to do so, not possible to read cfgrib directly to memory
    # without first saving to disk. As a result we need to download the grib file
    # and rename it w/ .grib extension to properly ingest it

    wget.download(nomad_call, out = 'tmp/temp_df.grib')
    wind_xr = xr.open_dataset('tmp/temp_df.grib', engine='cfgrib')
    
    if out_type == 'xarray':
        return wind_xr

    wind_df = wind_xr.to_dataframe()

    if out_type == 'pandas':
        return wind_df
    elif out_type == 'csv':
        wind_df.to_csv(csv_path)


if __name__ == "__main__":

    nomad = retrieve_nomad(out_type='csv')
    pass
