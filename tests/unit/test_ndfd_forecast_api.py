from pathlib import Path
import pandas as pd
import pytest
import datetime
# this is used to be able to re-import to test config settings
import importlib
import ewxndfd.ndfd_forecast_api
from ewxndfd import ndfd_forecast_api as ndfd
import logging
logger = logging.getLogger(__name__)


@pytest.fixture
def lat_lon():
    return ndfd.LANSING_LAT_LON

def test_user_agent_from_env(monkeypatch):
    """Test that we can set the user agent in the environment"""
    
    tmp_user_agent = "(nowhere.com, noboday@nowhere.com)"
    monkeypatch.setenv("NDFD_USER_AGENT", tmp_user_agent )
    
    # since this config value is set at import time, re-import to get the new value
    importlib.reload(ewxndfd.ndfd_forecast_api)
    from ewxndfd.ndfd_forecast_api import DEFAULT_USER_AGENT
    assert DEFAULT_USER_AGENT==tmp_user_agent
    
def test_construct_ndfd_url_includes_lat_lon_and_unit():
    lat, lon = ndfd.LANSING_LAT_LON
    url = ndfd.construct_ndfd_digital_forecast_url(lat, lon)
    assert f"lat={lat}" in url
    assert f"lon={lon}" in url
    assert "Unit=m" in url
    assert "product=time-series" in url


def test_request_ndfd_digital_forecast(lat_lon):
    lat, lon = lat_lon
    response = ndfd.request_ndfd_digital_forecast(lat, lon)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/xml;charset=UTF-8'
    assert "ERROR" not in response.text.upper()  # basic check for no error in response content 


def is_numeric(obj):
    """ this helps identify the Pandas numpy numeric types """
    attrs = ['__add__', '__sub__', '__mul__', '__truediv__', '__pow__']
    return all(hasattr(obj, attr) for attr in attrs)

def test_units_parameter(lat_lon):
    
    lat, lon = lat_lon

    test_units_value = "metric"
    df_metric = ndfd.daily_forecast_summary(lat = lat, lon = lon, units = test_units_value)
    assert isinstance(df_metric , pd.DataFrame)

    test_units_value = "us"
    df_us = ndfd.daily_forecast_summary(lat = lat, lon = lon, units = test_units_value)
    assert isinstance(df_us , pd.DataFrame)

    # the column names from NDFD include the units 
    temperature_columns = [
            ("Daily Minimum Temperature (Celsius)","Daily Minimum Temperature (Fahrenheit)"),
            ("Daily Maximum Temperature (Celsius)", "Daily Maximum Temperature (Fahrenheit)")
            ]
    
    for temp_column in temperature_columns:
        temp_metric_series = df_metric[temp_column[0]].dropna()
        temp_us_series = df_us[temp_column[1]].dropna()

        assert not temp_metric_series.empty
        assert not temp_us_series.empty

        temp_metric = float(temp_metric_series.iloc[0])
        temp_us = float(temp_us_series.iloc[0])
    
        assert isinstance(temp_metric, float)
        assert isinstance(temp_us, float)
    
        temp_diff = abs(temp_us - ((temp_metric * 1.8) + 33) )
        assert  temp_diff < 2
    
    
def test_daily_forecast_summary_using_sample_xml(lat_lon):
    
    lat, lon = lat_lon
    df = ndfd.daily_forecast_summary(lat, lon)
    assert isinstance(df, pd.DataFrame)
    # expect humidity summary columns
    assert any('Maximum' in c and 'Relative Humidity' in c for c in df.columns)
    # expect min and max temperature metric columns (names taken from XML)
    assert any('Daily Minimum Temperature' in c for c in df.columns)
    assert any('Daily Maximum Temperature' in c for c in df.columns)
    # DataFrame should have at least one row
    assert df.shape[0] > 0
    
    # check that first row of date column is a valid date
    first_date =  df.loc[1,"forecast_date"]
    assert isinstance(first_date, datetime.date)
    
    
    first_relh = df.loc[1, "Maximum Relative Humidity (percent)"]
    assert is_numeric(first_relh)
    
