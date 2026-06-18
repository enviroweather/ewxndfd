# ewxNDFD: forecast data for the Enviroweather MesoNet

ewxNDFD is a Python package to collect and transform weather forecast data from
the National Digital Forecast Database (NDFD) gridded weather forecast.  It was 
created specifically for used by [MSU Enviroweather](https://enviroweather.msu.edu)
but may be useful for other applications needing daily forecast summaries by coordinate. 

This project is currently in early stages and under heavy development. 

MSU Enviroweather previously collected forecast data from NDFD by grid, downloading
GRIB files and extracting values. This is the successor to that system with 
the goal of pulling data as needed from the excellent NWS / NDFD REST API system.

Thank you and acknowlegement to the array of offices, programs, and staff within
the US NOAA who develop, caclulate, and distribute these forecasts.  We thank 
the regional US weather offices that review and adjust the forecasts and make 
them freely available soprograms like Enviroweather can provide guidance for our
agricultural community.

## About the ouptut

The main output of this package is a daily forecast table in the form, for example
from the command `ndfd_daily -lat 42.73 -lon -84.44 --location LAN`

(note currently there is a bug for first/last day min/max temperature )

| forecast_date | Location | Maximum Relative Humidity (%) | Minimum Relative Humidity (%) | Maximum Wind Speed (m/s) | Mean Wind Speed (m/s) | Total Liquid Precipitation (cm) | Daily Min Temp (°C) | Daily Max Temp (°C) | latitude | longitude |
|---------------|----------|--------------------------------|--------------------------------|---------------------------|------------------------|-----------------------------------|----------------------|----------------------|----------|-----------|
| 2025-12-16    | LAN      | 88                             | 71                             | 8                         | 6.13                   | 0.0                               | -2.0                 | 2                    | 42.73    | -84.44    |
| 2025-12-17    | LAN      | 96                             | 76                             | 8                         | 4.61                   | 0.0                               | -3.0                 | 4                    | 42.73    | -84.44    |
| 2025-12-18    | LAN      | 96                             | 89                             | 8                         | 7.00                   | 0.84                              | -7.0                 | 7                    | 42.73    | -84.44    |
| 2025-12-19    | LAN      | 96                             | 68                             | 7                         | 5.50                   | 0.03                              | -7.0                 | -3                   | 42.73    | -84.44    |
| 2025-12-20    | LAN      | 79                             | 70                             | 6                         | 5.25                   |                                   | -6.0                 | 3                    | 42.73    | -84.44    |
| 2025-12-21    | LAN      | 96                             | 78                             | 3                         | 2.75                   |                                   | -8.0                 | -1                   | 42.73    | -84.44    |
| 2025-12-22    | LAN      | 88                             | 71                             | 3                         | 2.00                   |                                   |                     



## Get started with the package

This program is not yet available on PyPI or conda.  To install the latest versiom, either 
1) obtain a copy of latest build in compressed or wheel form from a developer, 
   file `ewxndfd-0.x.x.tar.gz` or `ewxndfd-0.x.x-py3-none-any.whl` 
   and install using pip, for example:
   
   `pip install /path/to/ewxndfd-0.0.1-py3-none-any.whl`

   (adjust version number as needed)

   it's a future goal to create releases on github to use from there

2) clone this repository and build the package locally (see Development and building below)
and install the built package file in the 'dist' folder using pip as above.

#### Using Conda

Currently this doesn't have a conda build.sh script, so use pip to install from 
a wheel file inside a conda environment.


## Development and building

This POC uses the [uv](https://docs.astral.sh/uv/) python project management tool

- install uv (see https://docs.astral.sh/uv/getting-started/installation/)
- clone this package 
- cd to ewxndfd directory
- to use the package, build using `uv build` which will create a wheel file in the dist/ directory
  and see instructions above for using in your project with a virtual environment
- to contribute/edit code, try running `uv run pytest` which will create a virtual environment in .venv if needed
  <!-- which should create a virtual environment named 'test' and run pytest in that environment. -->
- some Enviroweather-specific tests require access to sample data, which are not included in this repository. 
  The location of there example files is currently hardcoded in the text code, along with the expected dates to check
  based on the files present.   
  Current setup: Copy NDFD CSV files (in ndfd_auto format) matching *_20251119*.csv 
  (for example `maxr_20251119t00.csv` ) into a directory /tests/ndfd_sample_files 

## Example usage

### combining with today's weather so far

The NDFD point forecast from this hourly API only includes hourly forecasts for the 
remainder of today.  If you need a daily forecast summary for today, you need to 
provide actual observations of that data for the coordinate of interest.   This
is not fully implemented yet, so the forecast summary for today will not be 
accurate until this is added.

This package is designed to allow you to provide your own actual hourly weather data, 
for example from a weather station, or other source, to combine with the NDFD forecast
data to create a full daily summary for today.  The actual hourly weather data
should be provided as a pandas DataFrame with a datetime index and columns
matching the expected variable names (see documentation for `daily_forecast_summary`
function for details).

A future direction is for the package to access observed weather data from a source like 
[NOAA ISD](https://www.ncei.noaa.gov/products/global-hourly) or python package 
like [Meteostat](https://dev.meteostat.net/python/) other source to combine with 
the NDFD forecast data to create a full daily summary for today.


### using inside python code

Once installed in your virtual environment, you can import and use the package in your python code.

```python
(lat, lon) = (42.7261, -84.4833)  # example coordinates for Lansing, MI
from ewxndfd.ndfd_forecast_api import daily_forecast_summary
daily_forecast_df = daily_forecast_summary(lat= lat
                                           lon = lon
                                           hourly_weather=None, 
                                           location_name="LAN")

print(daily_forecast_df)

```


#### parameters:

- `lat` Latitude in decimal degrees (-90..90), for example 42.73 (required)

- `lon` Longitude in decimal degrees (-180..180), for example -84.44 (required)

- `hourly_weather` include hourly weather y/n, set to None to exclude all hourly data

- `user_agent` User-Agent header to send with requests, defaults to (enviroweather.msu.edu, ewx@enviroweather.msu.edu)
   strongly suggested by the NDFD service to help them understand client base.  enter a value here
   to override the default. 

   You can more consistently override this user agent (rather than including it in all commands) by setting
   the environment variable `NDFD_USER_AGENT` to a string with the name and email in parenthesis, like 
   `'(url, email)'`  If setting this variable with a shell command you may have to enclose in single quotes
   so that the parenthesis are not interpreted by the shell, for example 
   `export NDFD_USER_AGENT='(enviroweather.msu.edu, ewx@enviroweather.msu.edu)'`


- `location_name` Optional value for Location column to key output, to enable combining with other locations
  This is useful if you are aggregating forecast data from multiple locations and need a location key column

### Command line interface (cli)

the package installed a command line interface `ndfd_daily` that can be used get
daily summaries NDFD forecast data for a specific location.  Example usage: 

```
 ndfd_daily --lat 42.7261 --lon -84.4833 --location LAN
``` 

The parameters are named slightly differently for CLI usage for clarity (no abbreviations). 


See the parameters list above or use `ndfd_daily --help`

-  --latitude LATITUDE, -lat LATITUDE
   Latitude in decimal degrees (-90..90), for example 42.73 (required)

-  --longitude LONGITUDE, -lon LONGITUDE
   Longitude in decimal degrees (-180..180), for example -84.44 (required)

-  --user-agent USER_AGENT
    User-Agent header to send with requests, defaults to (enviroweather.msu.edu, ewx@enviroweather.msu.edu)
    strongly suggested by the NDFD service to help them understand client base.  enter a value here
    to override the default.   

-  --location LOCATION   
   Optional value for Location column to key output, to enable combining with other locations
   This is useful if you are aggregating forecast data from multiple locations and need a location key column

### Example Notebooks

Python notebooks in the /notebooks folder provide example usage of the package.
These notebooks require the ewxndfd package to be installed in the python environment
used to run the notebooks.

### Enviroweather Only Usage: 

For working with data files generated by the NDFD_Auto seriesof scripts, 
use the following example code.  You must have access to a folder with
the current Enviroweather-formatted NDFD forecast files, and provide the path to that
folder in the code below.

```python
path_to_ndfd = "/data/some/place/ndfd"
from ewxndfd import NDFD, DAILY_NDFD_VARIABLE_TYPES 

# example, show all the variable names available
print(DAILY_NDFD_VARIABLE_TYPES)

# pull out  7 day forecasted minimum temperature for all possible 
# enviroweather stations 
ndfd = NDFD(path_to_ndfd, variable_type="mint")
ndfd_data = ndfd.get_forecast()

#print first 10 rows
print(ndfd_data[0:10])

# convert to long format as a first step in importing into a database
# this is a work in progress and API/syntax will change! 
mint_fcst = n._wide_to_long(ndfd_data)
print(mint_fcst[0:10])

``` 

## About NDFD

NDFD is a large office and offers many products from different offices and has 
documentation in different places.  This attempts to list relevant links for the
data we are using. 

#### Point level data

The main service this package use is the [Point data from National Digital Forecast Database]
(https://vlab.noaa.gov/web/mdl/ndfd-point-data) (NDFD) via a 
Representational State Transfer (REST) XML Web Service, documented on

https://graphical.weather.gov/xml/rest.php

[Guidelines for using this service](https://graphical.weather.gov/xml/mdl/XML/Design/WebServicesUseGuidelines.php)

The NDFD is updated 25 and 55 minutes after the hour. A future feature for this
package is to cache forecasts downloaded to prevent redownloading the same data
Not that the the authors' use of this library is to save the results in a 
database and only downloads the latest data once per point. 

This library uses the **Single Point Unsummarized Data** from 

https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php

See the documentation on the page above for details about the input parameters. 

A example URL or API query that works with this service is: 

`https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?Unit=m&lat=42.73&lon=-84.55&product=time-series&maxt=maxt&mint=mint&rh=rh&wspd=wspd&qpf=qpf`

which returns values in metric units for maximum temperature (maxt), minimum temperature (mint), relative humidity (rh), 
wind speed (wspd), and liquid precipitation (qpf) for the lat/lon coordinate 42.73, -84.55 from the current day for the 
time remaining to the end of the forecast period.

Adding in historical dates does not return previous NDFD forecasts. this service only returns the latest forecast 
available.  Setting an end date in the API can limit the forecast period returned to reduce the load on federal servers, 
but this python library doesn't use that and always returns 7 days. 




The variables available from this service are documented on the [NDFD Element Names](https://graphical.weather.gov/xml/docs/elementInputNames.php) Page, however not all of these elements 
may be available from the example API above. 



#### Metadata description
This page is from the NDFD GIS group, and describes variables that appear in 
GIS files (e.g. GRIB files) but should apply to the data available from the point
API (digital
)
## Copyright

- Copyright © 2025 MSU Trustees
- Free software distributed under the [MIT License](./LICENSE).
