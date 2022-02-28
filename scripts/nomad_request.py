from re import L
from unittest.mock import NonCallableMagicMock
import urllib.request as rq
import datetime
import math
from pandas import DataFrame
import xarray as xr
import xarray_extras.csv as xcsv
import os
import numpy as np
import wget
import pandas as pd

def retrieve_nomad(
    call_date,
    call_time,
    lead_time=0,
    lat_range=(-90, 90),
    lon_range=(0, 360),
    out_type="xarray",
    temp_dir="../tmp/",
):
    """
    Retrieves GFS predictions via NOMAD API, optionally filtering to a specific
    lat/lon window. By default, returns an xarray object - other options are
    csv and pandas.DataFrame().

    Inputs:
        call_date: str of YYYYMMDD gfs forecast to collect
        call_time: str, one of {'00', '06', '12', '18'}
        lead_time: int, forecast to collect in number of hours from start
        lat_range: (tuple) of minimum, maximum lat in degrees
        lon_range: (tuple) of minimum, maximum lon in degrees
        out_type: one of {'xrray', 'csv', 'pandas'}
        csv_path: if out_type is 'csv', path to save csv

    Output:
        An xarray object, pandas dataframe, or None (with a csv saved to the
        csv path)

    """

    # download the most recent GFS predictions via NOMAD, optionally subset to
    # specific latitude/longitude window

    if lead_time and lead_time > 0:
        lead_format = "f" + str(lead_time).zfill(3)
    else:
        lead_format = "anl"

    nomad_par = {
        "date_format": call_date,
        "lat_min": lat_range[0],
        "lat_max": lat_range[1],
        "lon_min": lon_range[0],
        "lon_max": lon_range[1],
        "hour_format": call_time,
        "lead_format": lead_format,
    }

    # surface level data from https://nomads.ncep.noaa.gov/
    nomad_call = (
        "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?"
        + "file=gfs.t{hour_format}z.pgrb2.0p25.{lead_format}"
        + "&lev_PV%5C%3D2e%5C-06_%5C%28Km%5C%5E2%2Fkg%2Fs%5C%29_surface=on"
        + "&all_var=on"
        + "&subregion="
        + "&leftlon={lon_min}&rightlon={lon_max}"
        + "&toplat={lat_max}&bottomlat={lat_min}"
        + "&dir=%2Fgfs.{date_format}%2F{hour_format}%2Fatmos"
    )
    nomad_call = nomad_call.format(**nomad_par)

    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    else:
        for file in os.scandir(temp_dir):
            os.remove(file.path)

    # we need to download the grib file and rename it w/ .grib extension
    # to properly ingest it using the cfgrib engine

    wget.download(nomad_call, bar=None, out=temp_dir + "temp_df.grib")
    wind_xr = xr.open_dataset(temp_dir + "temp_df.grib", engine="cfgrib")

    if out_type == "xarray":
        return wind_xr

    wind_df = wind_xr.to_dataframe()

    if out_type == "pandas":
        return wind_df
    elif out_type == "csv":
        wind_df.to_csv(temp_dir + "temp_df.csv")


def combine_forecasts(
    lead_time=0,
    lead_interval=1,
    lat_range=(-90, 90),
    lon_range=(0, 360),
    temp_dir="../tmp/",
    call_date=None,
    call_time=None,
    verbose=False,
    out_path=None
):
    '''
    Loops over all available forecasts according to lead_time and lead_interval,
    combining into a csv.

    Inputs:
        lead_time: (int), forecast to collect in number of hours from start
        lead_interval: (int), intveral for forecast collection (min 1)
        lat_range: (tuple) of minimum, maximum lat in degrees
        lon_range: (tuple) of minimum, maximum lon in degrees
        temp_dir: (str) of folder to save temporary files
        call_date: (str) of YYYYMMDD gfs forecast to collect
        call_time: (str) one of {'00', '06', '12', '18'}
        verbose: (bool) of whether to print status messages
        out_path: (str) path to save combined csv
    
    Outputs:
        None but out_path will be populated with combined csv
    '''

    if not call_time:
        # if no call time, coarsen current time to most recent 6-hour interval
        call_time = str(math.floor(datetime.datetime.now().hour / 6) * 6).zfill(2)

    if not call_date:
        call_date = datetime.datetime.now().strftime("%Y%m%d")

    lead_times = np.arange(0, min(lead_time + 1, 121), lead_interval)
    if lead_time > 120:
        lead_times = np.concatenate(
            [
                lead_times,
                np.arange(
                    123,  # After 120, forecasts come at 3 hour intervals
                    min(lead_time, 385) + 3,  # Max lead is 384
                    math.floor(lead_interval / 3) * 3 + 3,  # Min interval is 3
                ),
            ]
        )

    if not out_path:
        out_path = "GFS_{0}_{1}_lead_{2}_by_{3}.csv".format(
            call_date, call_time, str(lead_time), str(lead_interval)
        )

    for idx, lead_time_idx in enumerate(lead_times):
        if verbose:
            print(
                "retrieving GFS {}_{} at lead hour {} ({:.0%} complete)".format(
                    call_date, call_time, lead_time_idx, idx / len(lead_times)
                )
            )

        lead_df = retrieve_nomad(
            call_date,
            call_time,
            lead_time=lead_time_idx,
            lat_range=lat_range,
            lon_range=lon_range,
            out_type="pandas",
            temp_dir=temp_dir,
        )

        lead_df.loc[:, "speed"] = (
            lead_df.loc[:, "u"] ** 2 + lead_df.loc[:, "v"] ** 2
        ) ** 0.5

        lead_df.loc[:, "dir"] = np.rad2deg(
            np.arctan2(lead_df.loc[:, "u"], lead_df.loc[:, "v"])
        )

        lead_df.loc[:, "lead_hours"] = lead_time_idx

        lead_df.rename(
            columns={"time": "forecast_time", "valid_time": "lead_time"},
            inplace=True
        )

        lead_df.drop(columns=["step", "potentialVorticity"], inplace=True)

        if not os.path.isfile(out_path):
            lead_df.to_csv(out_path, header="column_names")
        else:
            lead_df.to_csv(out_path, mode="a", header=False)

    if verbose:
        print("Successfully retrieved GFS data, saved to: \n" + out_path)


def retrieve_closest_points(nomad_df, lat_lon, var_list = None):
    """
    Given a latitude or longitude, returns the four closest GFS
    forecast locations.lead_time

    Inputs:
        nomad_df: GFS dataset in either xarray.DataSet or pd.DataFrame format
        lat_lon: (tuple) latitude and latitude of survey location
        var_list: list of variables of interest

    Output:
        a sliced pandas dataframe, with the four closest GFS points
    """

    if not var_list:
        var_list = nomad_df.columns

    lat, lon = lat_lon
    lat_coursened = (math.floor(lat * 4) / 4, math.ceil(lat * 4) / 4)
    lon_coursened = (math.floor(lon * 4) / 4, math.ceil(lon * 4) / 4)

    if isinstance(nomad_df, xr.Dataset):
        geo_mask = {
            "latitude": lat_coursened,
            "longitude": lon_coursened
        }
        sliced = nomad_df.sel(geo_mask)[var_list]

    elif isinstance(nomad_df, pd.DataFrame):
        geo_mask = np.logical_and(
            nomad_df.latitude.isin(lat_coursened),
            nomad_df.longitude.isin(lon_coursened)
        )
        sliced = nomad_df.loc[geo_mask, var_list]

    return sliced
