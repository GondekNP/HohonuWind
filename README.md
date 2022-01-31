# HohonuWind
The goal of the project is to pull surface wind data from the national weather service, Global Forecasting System (GFS), and National Center for Environmental Prediction (NCEP).

Objectives: 

- A script for retrieving wind data from the NWS
- A schema design for the wind data table that Hohonu should add to their postgres
database. This can be defined in a SQL script or DBML (https://www.dbml.org/)
- A data merging script that given a location will give you the nearest 4 wind data points
(since the wind data is defined on a grid).


Questions: 

- Does Hohonu want a single postgres table with just the most recent GFS predictions, or do they want future predictions going forward days/hours?
- Which metrics are most useful to them?
- Do previous predictions need to persist or should the table be updated with most recent/relevant predictions?
- What projection/coordinate reference system does Hohonu use internally? Will this table be linked via a foreign key to any other tables in Hohonu's DBMS or will it exist solely for the utility providing wind data at the four closest points?