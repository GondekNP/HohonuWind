from xmlrpc.client import boolean
import nomad_request
import numpy as np
import argparse

parser = argparse.ArgumentParser()


## Required arguments - how many forecasts to retrieve, and at what interval?
parser.add_argument(
        'lead_time', type=int,
        help="Retrieve forecasts up to (start_time + lead_time)"
    )
parser.add_argument(
        'lead_interval', type=int,
        help="Retrieve forecasts every lead_interval hours"
     )

## Optional arguments

parser.add_argument(
        '--global', action='store_true', required=False,
        help="If true, gather GFS forecasts from entire" +\
             "world rather than North America only"
     )
parser.add_argument(
        '--forecast_date', type=str, required=False,
        help="If specified, rather than collecting most recent forecasts," +\
             " collect forecasts from a given forecast_date. Must be in" +\
             " YYYYMMDD format and within the last 9 days of call time."
     )
parser.add_argument(
        '--forecast_time', type=str, required=False,
        help="If specified, rather than collecting most recent forecasts," +\
             " collect forecasts from a given forecast_time. Must be one of" +\
             " '00', '06', '12', '18', as these are when GFS forecasts release."
     )

args = parser.parse_args()

