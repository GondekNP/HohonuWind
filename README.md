# HohonuWind
The goal of the project is to pull surface wind data from the national weather service, Global Forecasting System (GFS), and National Center for Environmental Prediction (NCEP).

Objectives: 

● A script for retrieving wind data from the NWS
● A schema design for the wind data table that Hohonu should add to their postgres
database. This can be defined in a SQL script or DBML (https://www.dbml.org/)
● A data merging script that given a location will give you the nearest 4 wind data points
(since the wind data is defined on a grid).
