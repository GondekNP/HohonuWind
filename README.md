The goal of the project is to pull surface wind data from the national weather service's Global Forecasting System (GFS) programatically, define functions for subsetting a particular location in the world (subsetting to the four closest grid locations), and incorporate all the information into PostgreSQL.

# Pulling and combining GFS data

Data can be pulled from the GFS NOMAD server using the `retrieve_gfs.py` script.

Basic usage can be called as:

```bash
python3 retrieve_GFS.py 384 1
```

which retrieves all surface wind speeds for North America available, starting with the most recent available forecast and retreiving every available lead forecast. For the first 180 hours from the start time, there will be a forecast for each hour, after which, every three hours until the maximum lead of 384.

Arguments (for use as bash flags) include:
- `lead time` - *REQUIRED* maximum lead time to obtain forecasts for
- `lead_interval` - *REQUIRED* interval to obtain forecasts. Function handles the change in availablity after lead of 120 hours by obtaining the closest available resolution to `lead interval` (1 hr interval available for the first 120 hours after forecast generation time, then every 3 hours untl 384).
- `all_global` - if present, forecasts will be obtained for the entire world
- `bbox int,int,int,int` - if present, forecasts will be obtained inside the specified bounding box. Note that GFS uses a window of (0,360) rather than (-180,180) for longitude, so may need to adjust by adding 180. 
- `forecast_date` - if present, rather than most recent forecast available, obtain the forecast generated on `forecast_date`. Only about 9 days of past data are preserved by GFS. 
- `forecast_time` - if present, rather than most recent forecast available, obtain the forecast generated at a given time of day. Since forecasts are generated four times a day, only options are {'00', '06', '12', '18'}.
- `verbose` - if present, print progress messages to console. 
- `out_path` - if present, write csv with custom name. Otherwise, it will be named with the date/time of the forecast being retrieved, the lead time, and the lead interval. 

For example, the following: 

```bash
python3 retrieve_GFS.py 4 1 --bbox 21,22,23,25 --forecast_date 20220223 --forecast_time 12 --verbose --out_path ../hawaii_test.csv 
```

Retrieves the first four hours of GFS forecast for Feb 23rd, 2022 at 12pm (12pm to 4pm), saving it to `hawaii_test.csv` in the root directory of the repo.

This function can be programatically called by a scheduler in order to systematically update the downstream postgres database with the most current available forecasts available. Anecdotally, it seems to take somewhere from 5 to 20 minutes for the forecasts to become available after they are scheduled for release, so further testing may be needed. Alternatively, a scheduler could start to ping for the dataset at the time of release (00, 06, 12, 18), triggering a download only when the ping is successful.

# Finding the four closest points to a given survey location

When the csv obtained is loaded as either a pd.DataFrame or xarray.DataSet in python, the closest point can be obtained using `nomad_request.retrieve_closest_points()` with the following arguments:

- nomad_df - GFS dataset in either xarray.DataSet or pd.DataFrame format
- lat_lon - (tuple) latitude and latitude of survey location
- var_list - list of variables of interest

For example, within the `scripts` folder:

```python
import pandas as pd
gfs_hawaii = pd.read_csv('../hawaii_test.csv')
nomad_request.retrieve_closest_points(gfs_hawaii, (21.22, 24.60), var_list = ['latitude', 'longitude', 'lead_time', 'speed'])
```

Returns the following sliced DataFrame:

```
     latitude  longitude            lead_time      speed
6       21.00      24.50  2022-02-23 12:00:00  42.597958
7       21.00      24.75  2022-02-23 12:00:00  34.673840
15      21.25      24.50  2022-02-23 12:00:00  25.371065
16      21.25      24.75  2022-02-23 12:00:00  35.784412
...
```

# Variables obtained and generated

Variables obtained directly from the NOMAD API as as follows:

- `u` - U-Component of Wind [m/s]
- `v` - V-Component of Wind [m/s]
- `t` - Temperature [K]
- `gh` - Geopotential Height [gpm]
- `pres` - Pressure [Pa]
- `vwsh` - 	Vertical Speed Shear [1/s]

Generated features are:
- `speed` - The 2-norm of U and V component of wind speed [m/s]
- `dir` - The direction of windspeed, computed using U and V component and np.arctan2. Represented in degrees.

# Suggested PostgresSQL setup

A suggested schema to house these data are located in `create_wind_table.sql`. The design of this table will depend on how the existing data are structured, however, recommendations are as follows:

- Table one - surface characteristics

```
CREATE TABLE wind_gfs (
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    forecast_datetime TIMESTAMP NOT NULL,
    lead_datetime TIMESTAMP NOT NULL,
    lead_hours SMALLINT NOT NULL,
    u REAL,
    v REAL,
    t REAL,
    gh REAL,
    pres REAL,
    vwsh REAL,
    speed REAL,
    dir REAL
    PRIMARY KEY(latitude, longitude, forecast_datetime)
);
```

This table will house the forecasts generated at a given forecast date. The combination of lat/lon/forecast_datetime is guaranteed to be unique, where lat/lon alone will not be assuming multiple forecasts are stored in the same table.

In order to preserve space, it is recommended that 'stale' forecasts (up to Hohonu's discretion) be archived in an AWS S3 bucket and dropped from the `wind_gfs` table periodically, likely alongside the download and ingestion of new forecasts.

If desired, in order to save the computational cost of downloading and subsetting wind forecast locations on demand, Hohonu can create a seperate link table as follows:

- Table two - sensor by grid forecast link

```
CREATE TABLE sensor_gfs (
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    sensor_id VARCHAR(8)
);
```

This approach would allow grid forecasts to be obtained for each sensor using a simple join or view:

- View - grid locations by sensor

```
CREATE VIEW grid_by_sensor AS
SELECT *
FROM sensor_gfs s, wind_gfs w
ON s.latitude = w.latitude
AND s.longitude = w.longitude
```

Using `grid_by_sensor`, or a join on the fly, Hohonu can define a custom function to calculate a representive value for each feature of interest, perhaps according to a distance metric to a each point (a KDE approach maybe):
