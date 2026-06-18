
from datetime import timezone, datetime, date, timedelta
from zoneinfo import ZoneInfo
import os
import csv

from ewxndfd.datetime_utils import is_utc,ensure_datetime_has_tz
from . import DEFAULT_TIME_ZONE    

DAILY_NDFD_VARIABLE_TYPES = {
    "maxr", #daily max relative humidity
    "minr", #daily min relative humidity
    "maxt", #daily max temperature
    "mint", #daily min temperature
    "qpfd"  #daily quantitative precipitation forecast
}

# Hourly variable types names, not used in forecast ETL yet
HOURLY_NDFD_VARIABLE_TYPES = {
    "relh", # hourly relative humidity
    "pops", # probability of precipitation
    "qpf6", # 6-hour quantitative precipitation forecast
    "temp", # hourly air temperature
    "wdir", # hourly wind direction
    "wspd"  # hourly wind speed
}


    
class NDFD():
    """Enviroweather Only: small class for finding, reading, filtering, and transforming NDFD
    forecast csv data files
    """
    
    def __init__(self, ndfd_dir:str, variable_type:str, unit_str:str, unit_abbr:str, tz:str=DEFAULT_TIME_ZONE):
        """initialize NDFDFile object for a specific weather variable

        Args:
            path (str): base path where NDFD files are found
            variable_type (str): type of weather variable
            unit_str (str): full unit string for variable
            unit_abbr (str): abbreviated unit string for variable
            tz (str): timezone string for local time zone

        Raises:
            ValueError: must be a valid variable type
            ValueError: NDFD directory must exist
        """
        
        
        # self.ndfd_dir(ndfd_dir) # set via property setter, validates path
        self.ndfd_dir = ndfd_dir

        # set variable type if it's valid to read-only value
        if variable_type not in DAILY_NDFD_VARIABLE_TYPES:
            raise ValueError(f"Invalid variable type: {variable_type}")
        else:
            self._variable_type = variable_type
        
        self.unit_str = unit_str
        self.unit_abbr = unit_abbr
                
        self.tz = tz
        
        self.ndfd_data_cache = []
        self.ndfd_file_path_cache = ""
        self.forecast_period = ""    
        

    @property
    def variable_type(self)->str:
        """Enviroweather Only: get the NDFD variable type for this object (read-only property)

        Returns:
            str: NDFD variable type
        """
        return(self._variable_type)
    
    
    @property
    def ndfd_dir(self)->str:
        """get the full path to the NDFD directory for this variable type

        Returns:
            str: full path to the NDFD directory
        """
        return(self._ndfd_dir)
    
    @ndfd_dir.setter
    def ndfd_dir(self, ndfd_directory_path:str):
        """Enviroweather Only set the full path to the NDFD directory on Enviroweather
        servers for this variable type

        Args:
            path (str): full path to the NDFD directory
        """
        if os.path.exists(ndfd_directory_path) is False:
            raise ValueError(f"NDFD directory does not exist: {ndfd_directory_path}")  
        
        self._ndfd_dir = ndfd_directory_path

        
    def contstruct_file_name(self, date_forecast_created:date, hour_forecast_created:int)->str:
        """Enviroweather only.  Create the file name for finding the previous version of 
        forecast data.  The filename is created based on the date time it was pulled, not 
        necessarily the date/hour it covers, and assume the cron job that pulls forecast data
        is on time. 
        
        Args:
            date_forecast_created (date) date as python date object
            hour_forecast_created (int) hour the forecast file was created
            
        """
        d = date_forecast_created.strftime("%Y%m%d")
        h = str(hour_forecast_created).zfill(2)
        ndfd_filename = f"{self.variable_type}_{d}t{h}.csv"
        return(ndfd_filename)
                    
    def forecast_file_for_utc_datetime(self, utc_dt:datetime)->str:
        """Enviroweather only.  Determine the NDFD forecast file that would be current for the given utc datetime   
        
        Args:
            utc_datetime (datetime): a utc datetime value     
        Returns:
            str: filename to the appropriate NDFD forecast file
        """
        
        if not is_utc(utc_dt):
            raise ValueError("utc_datetime must be in utc timezone")
        
        hour = utc_dt.hour
        if hour < 6:
            forecast_hour = 0
        elif hour < 12:
            forecast_hour = 6
        elif hour < 18:            
            forecast_hour = 12
        else:
            forecast_hour = 18
            
        forecast_date = utc_dt.date()
        
        ndfd_filename = self.contstruct_file_name(forecast_date, forecast_hour)
        return(ndfd_filename)

    def forecast_file_for_local_datetime(self, dt:datetime)->str:
        """Enviroweather Only. given any datetime in local timezone, construct NDFD forecast file 

        Args:
            dt (datetime): local datetime, will be assigned local timezone if not timezone aware

        Returns:    
            str: filename of the NDFD forecast file
        """
        dt = ensure_datetime_has_tz(dt, self.tz)
        utc_dt = dt.astimezone(timezone.utc)
        return self.forecast_file_for_utc_datetime(utc_dt)  
    
    def recent_forecast_file(self)->str:
        """Enviroweather only. determine the most recent NDFD forecast file based on current local time 
        Returns:
            str: full path to the NDFD forecast file for the current time
        """
        local_datetime = datetime.now(timezone = self.tz)
        utc_datetime = local_datetime.astimezone(timezone=timezone.utc)
        forecast_file = self.forecast_file_for_utc_datetime(utc_datetime)
        return(forecast_file)
    
    def get_forecast(self, local_datetime:datetime=None, station_list:list=[])->list[dict]:
        """Enviroweather only.  Read NDFD forecast data for the given local datetime.  If no datetime is provided,
        use the current local datetime

        Args:
            local_datetime (datetime, optional): local datetime value. Defaults to None.    
        Returns:
            list: list of dicts representing NDFD data,suitable for importing into Pandas
        """
        if local_datetime is None:
            local_datetime = datetime.now(tz=ZoneInfo(self.tz))
        
        ndfd_filename = self.forecast_file_for_local_datetime(local_datetime)
        ndfd_file_path = os.path.join(self.ndfd_dir, ndfd_filename)
        
        if not os.path.exists(ndfd_file_path):
            raise FileNotFoundError(f"NDFD forecast file not found: {ndfd_file_path}")
        
        try:
            ndfd_data = self._read(ndfd_file_path)
        except Exception as e:
            raise RuntimeError(f"NDFD forecast file not found: {ndfd_file_path}") from e
        
        if station_list:
            ndfd_data = self.filter_stations(station_list)
 
        # ndfd_data = self._wide_to_long(ndfd_data)
            
        return(ndfd_data)
    
    
    def _read(self, ndfd_file_path:str)->list[dict]:
        """ Enviroweather Only. read NDFD file into list of dicts   
        Args:
            ndfd_file_path (str): full path to NDFD file
        Returns:
            list: list of dicts representing NDFD data,suitable for importing into Pandas DataFrame
        """

        if not os.path.exists(ndfd_file_path):
            raise FileNotFoundError(f"NDFD file not found: {ndfd_file_path}")  
        
        with open(ndfd_file_path, 'r') as file:
            reader = csv.DictReader(file)   
            ndfd_data = [row for row in reader]
        
        # reduce IO, cache the last read file and data
        # not sure if we will use this
        self.ndfd_file_path_cache = ndfd_file_path
        self.ndfd_data_cache = ndfd_data
        
        return ndfd_data
    
        
    def _wide_to_long(self,ndfd_data:list[dict])->list:
        """Enviroweather Only. convert NDFD format with one data per column for use with ETL processes"""
        
        long_data = []
        
        for row in ndfd_data:
            station = row['station']
            for column, value in row.items():
                # loop through columns keys and convert to rows
                # skip station key, we already have that
                if column == 'station':
                    continue
                
                # extract the date from date range
                fcst_dt = column.strip()                                                 
                d1 = fcst_dt.split('-')[0]
                forecast_date = date.fromisoformat(d1)
                
                forecast_value = float(value)
                long_row = {
                    'station': station,
                    'forecast_date': forecast_date,
                    self.variable_type: forecast_value
                }
                
                long_data.append(long_row)
        
        return long_data
    
    
    def filter_stations(self, station_list)->list:
        """Enviroweather Only. filter NDFD data to only include stations in station_list """

        station_list = [s.strip() for s in station_list]
        
        filtered_data = [d for d in self.ndfd_data if d['station'] in station_list]
        # optional self.ndfd_data = filtered_data
        return(filtered_data)

