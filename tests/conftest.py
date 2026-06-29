from pathlib import Path
import sys


# Ensure tests import local source tree first (src layout project).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
	sys.path.insert(0, str(SRC_PATH))


# alternative test value

test_lat = 43.72
test_lon = -85.5
test_station = 'grr'
test_weather_gov_url = "https://forecast.weather.gov/MapClick.php?x=160&y=71&site=grr&map_x=160&map_y=71" # test url from weather gov for test above
ALT_LAT_LON = (42.73, -84.55) 
ALT_STATION = (42.73, -84.55) 
