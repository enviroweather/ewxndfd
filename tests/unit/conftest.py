import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os   

import logging


FIXTURE_DIR = Path(os.path.dirname(os.path.realpath(__file__))).parent  / 'ndfd_sample_files'

@pytest.fixture
def v_type():
    return 'mint'

@pytest.fixture
def sample_dir():
    return FIXTURE_DIR 

@pytest.fixture
def sample_datetime():
    return datetime(2025, 11, 19, 2, 0, tzinfo=ZoneInfo("US/Eastern"))

@pytest.fixture
def sample_ndfd_mint():
    return  'mint_20251119t06.csv'
