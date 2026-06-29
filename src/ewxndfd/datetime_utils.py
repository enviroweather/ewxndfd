"""Datetime utility module for Enviroweather"""

from datetime import timezone, datetime, date, timedelta
from zoneinfo import ZoneInfo
import logging
logger = logging.getLogger(__name__)

DEFAULT_TZ = "US/Eastern"

def has_timezone(dt:datetime)->bool:
    """
    determine if a datetime value is timezone aware
    
    Args:
        dt (datetime): a datetime value to check   
        
    Returns:
        bool: True if the datetime has timezone info, False otherwise
        
    
    """    
    if dt.tzinfo is not None:
        if dt.tzinfo.utcoffset(dt) is not None:
            return True
        
    return False


def ensure_datetime_has_tz(dt:datetime, tz:str="UTC")->datetime:
    """determine if a datetime value is timezone aware, and if not, 
    assign the timezone set for this object

    Args:
        dt (datetime): a datetime value that is ostensibly local time
        tz (str, optional): Valid timezone string, Defaults to UTC

    Returns:
        datetime: 'timezone aware' datetime,  with a timezone as
    """
    
    if not has_timezone(dt):        
        dt = dt.replace(tzinfo=ZoneInfo(tz))
            
    return dt

def datetime_to_utc(local_datetime:datetime, tz=None)->datetime:
    """convert a local datetime to utc datetime.  If the local datetime is not timezone aware,
    assign the timezone set for this object
    Args:
        local_datetime (datetime): local datetime value, ostensibly in the object's timezone
        timezone (str, optional): valid timezone string. Defaults to None, which uses object's timezone.
    Returns:
        datetime: utc datetime value
    """      
    
    
    if not has_timezone(local_datetime) and tz is None:
            raise ValueError("tz must be provided for naive datetime values when converting to utc")
    
    if has_timezone(local_datetime) and tz is not None:
        raise ValueError("tz should not be provided for timezone aware datetime values when converting to utc") 
    
    # give it the timezone if it doesn't have one
    local_datetime = ensure_datetime_has_tz(local_datetime, tz) 
    utc_datetime = local_datetime.astimezone(timezone=timezone.utc)
    
    
    return utc_datetime

def is_utc(dt:datetime)->bool:
    """determine if a datetime value is in utc timezone

    Args:
        dt (datetime): a timezone aware datetime value  
    Returns:
        bool: True if the datetime is in utc timezone, False otherwise  
        
    """
    if not has_timezone(dt):
        return False
    
    if dt.tzinfo == timezone.utc:
        return True
    
    return False




