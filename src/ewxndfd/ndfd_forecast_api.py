#!/usr/bin/env python3
"""methods to get unsummarized/ detailed forecast from the NDFD XML api and 
summarize by day
"""
DEBUG=True

import logging
logging.basicConfig(level=logging.DEBUG)

import requests
import xml.etree.ElementTree as ET
import pandas as pd
from tabulate import tabulate
import argparse
import sys
from datetime import date # , timedelta, datetime
from os import getenv

PKG_VERSION="202606261745"

# configuration/constants
# this is set a import time
DEFAULT_USER_AGENT = getenv('NDFD_USER_AGENT', '(enviroweather.msu.edu, ewx@enviroweather.msu.edu)') 
# for testing
LANSING_LAT_LON = (42.78, -84.6)  # approximate lat/lon for Lansing, MI
UNITS_METRIC='m'
UNITS_US='e'

# TODO create a data type for units using this a constructor/setter
#  for proper api doc and 
def metric_or_us(units:str|None)->str:
    """ simple switch from US to metric units by checking if units look like metric units 
    if the unit specifier doesn't look like "metric" then use US units, because 
    there could be many ways to specify US units.  
    if it's blank then default is metric (because it should be metric!! )
    
    Args:
        units (str or None): human useable spec for units.   see description but 'metric' or somethingelse
        

    Returns:
        str: the short code used by NDFD API to specify units, which are defined by constants above
        because the short code for US units is 'e' which I never would have guessed
    """
    

    if not(units) or units.lower() in ['metric', 'scientific', 'm']:
        unit_parameter_value = UNITS_METRIC
    else:
        unit_parameter_value = UNITS_US
    
    return unit_parameter_value


def construct_ndfd_digital_forecast_url(lat, lon, begin=None, end=None, units=UNITS_METRIC):
    
    
    # dwml by default, not summarized 
    base_url = "https://digital.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php"
    
    if begin is None:
        date_today =  date.today().isoformat() + "T00:00:00"
    else:
        date_today = begin
        
    if end is None:
        date_future = '2030-04-20T00:00:00'
    else:
        date_future = end
    
    units_param_value = metric_or_us(units)
    units_param = f"Unit={units_param_value}"
    
    metrics = ['maxt', 'mint', 'rh', 'wspd', 'qpf']
    metrics_param = '&'.join([f"{m}={m}" for m in metrics])  # maxt=maxt&mint=mint...
    
    forecast_params = f"Unit=m&lat={lat}&lon={lon}&product=time-series&begin={date_today}&end={date_future}&{metrics_param}&{units_param}"
    
    forecast_url = f"{base_url}?{forecast_params}"
    
    return forecast_url

def request_ndfd_digital_forecast(lat:float, lon:float, user_agent:str = DEFAULT_USER_AGENT, units:str='metric'):
    
    date_today =  date.today().isoformat() + "T00:00:00"
    date_future = '2030-04-20T00:00:00'  
    
    forecast_url = construct_ndfd_digital_forecast_url(lat, lon, begin=date_today, end=date_future, units = units) # f"{base_url}?{forecast_params}"
    headers = {"User-Agent": user_agent}
    
    forecast_response = requests.get(forecast_url, headers=headers)
    return(forecast_response)
    

def get_start_end_times(root, time_layout_key):
    time_layouts = root.findall('.//time-layout')
    # only way to find what we want is to loop through all and find a match..?
    for tl in time_layouts:
        layout_key = tl.find('layout-key').text
        if layout_key == time_layout_key:
            start_times = [st.text for st in tl.findall('start-valid-time')]
            end_times = [et.text for et in tl.findall('end-valid-time')]
            return (start_times, end_times)
    return ()

def get_end_times(root, time_layout_key):
    time_layouts = root.findall('.//time-layout')
    for tl in time_layouts:
        layout_key = tl.find('layout-key').text
        if layout_key == time_layout_key:
            start_times = [st.text for st in tl.findall('end-valid-time')]
            return start_times
    return []

def get_start_times(root, time_layout_key):
    time_layouts = root.findall('.//time-layout')
    for tl in time_layouts:
        layout_key = tl.find('layout-key').text
        if layout_key == time_layout_key:
            start_times = [st.text for st in tl.findall('start-valid-time')]
            return start_times
    return []

#################################
## TODO !!! using the start times is a problem b/c the startime of low temp is the 
# day before today if it's early in the morning  for min temp. 
# that convert the date for min temp to yesterday, which is incorrect! 
# this may NOT be true for max temps or other things. 
# need to run the test in ndfd_api.ipynb to see what the start/end times look like
# OR figure out a better way to get the date from these for converting to  day 
def weather_metric_xml_to_df(root, metric_path:str)->pd.DataFrame:
    """create a date frame for single daily forecast value and date 
    by pulling data from the XML.  The valid times are a range (which
    must be looked up in the XML), so use the 'end' datime for 
    determining the 'date' of the forecast (since they sometimes start
    the day before, e.g. min temp).  sometimes the time window for a 
    forecast has gone by for min temp, so there is no forecast - it's assumed
    the value is now known.  in that case add a row with an NA value for today
    so it's consistent with other values for combining

    Args:
        root (ElementTree something): a 'root' object from ElementTree library, XML data
        metric_path (str): the XML path search value to find the observation we want
    Returns:
        pd.DataFrame: a data frame of 7 daily forecast values including today
    """
    
    logging.debug(f"extracting {metric_path} into df")

    weather_values = root.find(metric_path)
    time_layout_key = weather_values.get('time-layout')
    start_times, end_times = get_start_end_times(root, time_layout_key)
    
    # pick the time to use for the forecast data
    # end_time is best for temps, but relh only has start time
    # so start with end time and if blank, fall back to start times
    forecast_times = end_times
    if  forecast_times == []:
          forecast_times = start_times
    values = [v.text for v in weather_values.findall('value')]
    
    df = pd.DataFrame(
        {
            'forecast_time': forecast_times,
            'value': values
        }
    )
    
    df['forecast_date'] = pd.to_datetime(df['forecast_time']).dt.date
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    # sometimes there is no forecast value for today, eig past time for min temp
    # if no value for today, then add a row with NA value
    if(not ( min(df['forecast_date']))==date.today()):
        # add to the end
        df.loc[len(df)] = {'forecast_time': None, 'value' : None, 'forecast_date': date.today()}
        # reorder and clean up index for merging with other values
        df = df.sort_values('forecast_date').reset_index(drop=True)
        
    
    # use the new <NA> types instead of numpy NaN   
    df_len = len(df)
    logging.debug(f"data frame {df_len} rows") 
    return pd.DataFrame.convert_dtypes(df.convert_dtypes())

def weather_metric_name_from_xml(root, metric_path):
    weather_values = root.find(metric_path)
    unit_name = weather_values.get('units')
    value_name = weather_values.find('name').text
    return f"{value_name} ({unit_name})"
    
    
def daily_forecast_summary(lat:float, lon:float, hourly_weather:str|None = None, location_name:str|None = None, add_coordinates:bool=True, units:str=UNITS_METRIC)->pd.DataFrame:
    """request a summary of daily forecast from NDFD reformat from XML format to CSV

    Args:
        lat (float): latitude
        lon (float): longitude
        hourly_weather (str, optional): currently not used. Defaults to None.
        location_name (_type_, optional): if set, adds a column "location" with this value for use as a grouping column. Defaults to None.
        add_coordinates (bool, optional): If true, add columns of the coordinates to each row of the output. Defaults to True.
        units (str, optional): Use US or Metric units based on string sent Defaults to UNITS_METRIC which is 'm'.  
            anything other than 'm' or 'metric' or blank/none will return US units.  See request_ndfd_digital_forecast() for details

    Raises:
        ValueError: if the value returned from the NDFD API is empty, there was a problem with input params. 
        ValueError: if a metric (temperature, humidity) is request that's not valid, will return no data and raise error

    Returns:
        pd.DataFrame : a pandas dataframe of forecasted weather info, summarized by day for those available.  
    """
    
    ######
    # add hourly weather into df here for today
    # the way it's added depends on the metric and how that's stored in df from the xml
    resp = request_ndfd_digital_forecast(lat=lat, lon=lon, units=units)
    # if resp has an error # note status code is always 200 even if params are invalid
    if "ERROR" in resp.text.upper():
        # extract error message from resp.text and put in raise msg
        print(resp.text)
        raise ValueError("Error retrieving NDFD digital weather data.")
        
        
    root = ET.fromstring(resp.text)
    
    # collect daily summaries for each metric.  The unique requirements of each 
    # metric are the path to find it in the XML and how to summarize it by day
    # to keep this easy to edit/copy&paste, re-using the variable name metric_df
    # and then deleting the df before the next metric to ensure there is no 
    # re-use causing bugs.  Since don't know how to to cleanly send the Pandas
    # Summary functions as parameters, just repeat the code for each metric
    
    metric_df_list = []
    
    # max/min temps are already reported daily
    metric_path = ".//temperature[@type='minimum']"
    metric_name = weather_metric_name_from_xml(root, metric_path)
    min_temperature_df = weather_metric_xml_to_df(root, metric_path)
    metric_df_list.append( 
        pd.DataFrame(
            { 
            f'{metric_name}': min_temperature_df.groupby('forecast_date')['value'].min()
            }
        )
    )
    
    metric_path = ".//temperature[@type='maximum']"
    metric_name = weather_metric_name_from_xml(root, metric_path)
    max_temperature_df = weather_metric_xml_to_df(root, metric_path)
    metric_df_list.append(    
        pd.DataFrame(
            { 
            f'{metric_name}': max_temperature_df.groupby('forecast_date')['value'].max()  
            }
        )
    )

    metric_path = './/humidity'
    
    metric_df = weather_metric_xml_to_df(root, metric_path)
    if metric_df.empty:
        raise ValueError(f"The element {metric_path} not found found in NDFD forecast XML.")
    metric_name = weather_metric_name_from_xml(root, metric_path)
    
    # humidity must be summarized 
    metric_df_list.append(
        pd.DataFrame(
        { 
            f'Maximum {metric_name}': metric_df.groupby('forecast_date')['value'].max(), 
            f'Minimum {metric_name}': metric_df.groupby('forecast_date')['value'].min()
        }
        )
    )
    del(metric_df)
    
    ## wind speed
    # disabled, not included in daily summary as it's a logical daily statistic 
    # but will be included in hourly forecast 
    # metric_path = './/wind-speed[@type="sustained"]'
    # metric_name = weather_metric_name_from_xml(root, metric_path)
    # metric_df = weather_metric_xml_to_df(root, metric_path)
    # metric_df_list.append(
    #     pd.DataFrame(
    #     { 
    #         f'Maximum {metric_name}':  metric_df.groupby('forecast_date')['value'].max(), 
    #         f'Mean {metric_name}':  metric_df.groupby('forecast_date')['value'].mean()
    #     }
    #     )
    # )
    # del(metric_df)
    
    metric_path = './/precipitation[@type="liquid"]'
    metric_name = weather_metric_name_from_xml(root, metric_path)
    metric_df = weather_metric_xml_to_df(root, metric_path)
    metric_df_list.append(
        pd.DataFrame(
        { 
            f'Total {metric_name}':  metric_df.groupby('forecast_date')['value'].sum()
        }
        )
    )
    
    del(metric_df)
    
    logging.debug("combining dfs")
    summary_df = pd.concat(metric_df_list, axis=1)    # [humidity_daily, min_temperature_daily, max_temperature_daily, windspeed_daily], axis=1)

    if add_coordinates:
        summary_df['latitude'] = lat
        summary_df['longitude'] = lon
    
    if location_name is not None:
        summary_df.insert(0,'Location', location_name)
        
    summary_df = summary_df.rename_axis('forecast_date').reset_index()
    
    return summary_df



def table_format(forecast_df:pd.DataFrame, output_fmt:str = "csv")->str:    
    
    if not(output_fmt):
        output_fmt = 'csv'
    else:
        output_fmt = output_fmt.lower()
     
    if output_fmt == 'csv':
        output_table = forecast_df.to_csv(index=False)

    elif output_fmt in ['markdown', 'md'] :  # aka markdown     
        # special check for 'markdown' format to allow that since easier to remember 
        # than github 
        output_table = tabulate(forecast_df, headers='keys', showindex=False, tablefmt="github")
    
    else:
        output_table = tabulate(forecast_df,  headers='keys', showindex=False, tablefmt=args.output)
    
    return(output_table)
    
def main():
    def _valid_lat(value: str) -> float:
        try:
            v = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"latitude must be a float: {value}")
        if v < -90.0 or v > 90.0:
            raise argparse.ArgumentTypeError(f"latitude out of range [-90, 90]: {v}")
        return v

    def _valid_lon(value: str) -> float:
        try:
            v = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"longitude must be a float: {value}")
        if v < -180.0 or v > 180.0:
            raise argparse.ArgumentTypeError(f"longitude out of range [-180, 180]: {v}")
        return v

    parser = argparse.ArgumentParser(
        prog="ndfd_forecast_api",
        description="""Retrieve point-level NDFD forecast values from 
        https://digital.weather.gov/xml/ API and return create a daily summary.  
        Optionally include a location name column. 
        For example:  
        ndfd_daily -lat 42.73 -lon -84.44 --location LAN"""
    )

    # required args 
    parser.add_argument("--latitude", "-lat", type=_valid_lat, required=True,
                        help="Latitude in decimal degrees (-90..90), for example 42.73 (required)")
    parser.add_argument("--longitude", "-lon", type=_valid_lon,required=True,
                        help="Longitude in integer decimal degrees (-180..180), for example -84.44 (required)")
    
    # optional args
    parser.add_argument("--user-agent", dest="user_agent", default=DEFAULT_USER_AGENT,
                        help=f"User-Agent header to send with requests, defaults to {DEFAULT_USER_AGENT}")
    
    parser.add_argument("--location", type=str, default=None,
                      help="Optional value for Location column to key output, to enable combining with other locations")
    
    parser.add_argument("--units", type=str, default="m",
                      help="Optional value to set requested units of observations, 'm', or 'metric'or anything else for  US")
    
    parser.add_argument("--output", type=str, default="csv", 
                       help="""optional string indicating type of output default is CSV.  options are csv, 'markdown',
    or any string format suppored by python tabulate https://github.com/astanin/python-tabulate#table-format""")

    args = parser.parse_args()


    try:
        daily_forecast_df = daily_forecast_summary(lat=args.latitude, 
                                                   lon = args.longitude, 
                                                   hourly_weather=None, 
                                                   location_name=args.location,
                                                   units = args.units
                                                   )
    except Exception as exc:
        logging.error(f"Error retrieving forecast: {exc}", file=sys.stderr)
        sys.exit(2)

    # which format?
    output_table = table_format(daily_forecast_df)
        
    # print output to stdout
    print(output_table) 
       
if __name__ == "__main__":
    main()

    
    