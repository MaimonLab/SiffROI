from typing import Any
import pytest
import numpy as np

@pytest.fixture(scope="function")
def download_test_data(tmp_path_factory)->np.ndarray[Any, np.dtype[np.float_]]:
   """ TODO: download a test data set for FourCorr online, rather than from the server """

   filedir = tmp_path_factory.mktemp("data")
   raise NotImplementedError()

pytest.fixture(scope="function")
def test_fourcorr_init(download_test_data):
   import fourcorr 
   from fourcorr import FourCorrAnalysis

   return FourCorrAnalysis(download_test_data)

