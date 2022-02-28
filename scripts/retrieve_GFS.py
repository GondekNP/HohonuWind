import nomad_request
import numpy as np
import datetime
import math
import argparse

parser = argparse.ArgumentParser()

## Required arguments - how many forecasts to retrieve, and at what interval?

parser.add_argument(
    "lead_time", type=int, help="Retrieve forecasts up to (start_time + lead_time)"
)
parser.add_argument(
    "lead_interval", type=int, help="Retrieve forecasts every lead_interval hours"
)

## Optional arguments

parser.add_argument(
    "--out_path",
    type=str,
    required=False,
    help="Path for combined csv of all desired forecasts",
)
parser.add_argument(
    "--all_global",
    action="store_true",
    required=False,
    help="If true, gather GFS forecasts from entire"
    + "world rather than North America only",
)
parser.add_argument(
    "--forecast_date",
    type=str,
    required=False,
    help="If specified, rather than collecting most recent forecasts,"
    + " collect forecasts from a given forecast_date. Must be in"
    + " YYYYMMDD format and within the last 9 days of call time.",
)
parser.add_argument(
    "--forecast_time",
    type=str,
    required=False,
    help="If specified, rather than collecting most recent forecasts,"
    + " collect forecasts from a given forecast_time. Must be one of"
    + " '00', '06', '12', '18', as these are when GFS forecasts release.",
)
parser.add_argument(
    "--verbose",
    action='store_true',
    required=False,
    help="If specified, print status messages and progress.",
)
parser.add_argument(
    "--bbox",
    type = str,
    required=False,
    help="If --all_global is false, use this as bounding box for GFS forecasts"
    + " to download. Formatted as lat_min,lat_max,lon_min,lon_max without"
    + " spaces or quotes."
)


args = parser.parse_args()

if args.all_global:
    lat_range = (-90, 90)
    lon_range = (0, 360)
elif args.bbox:
    parsed_bbox = args.bbox.split(',')
    lat_range = (int(parsed_bbox[0]), int(parsed_bbox[1]))
    lon_range = (int(parsed_bbox[2]), int(parsed_bbox[3]))
else:
    lat_range = (7, 73)
    lon_range = (9, 222)

nomad_request.combine_forecasts(
    lead_time=args.lead_time,
    lat_range=lat_range,
    lon_range=lon_range,
    lead_interval=args.lead_interval,
    call_date=args.forecast_date,
    call_time=args.forecast_time,
    verbose=args.verbose,
    out_path=args.out_path
)

