""" Tests for generic ROI saving and loading """

import pytest
import numpy as np

@pytest.fixture(scope = "module")
def test_saving(tmp_path_factory):
    from siffroi import ROI

    from scipy import datasets

    racoon = datasets.face().T

    filedir = tmp_path_factory.mktemp("roi_temp")

    test_ROI = ROI(
        mask = racoon > 100,
        name = "test_ROI",
        slice_idx = None,
        info_string = "test info string",
    )

    test_ROI.save(filedir)

    return filedir

def test_load_ROI(test_saving):
    from siffroi import ROI, NoROIError

    load_path = test_saving
    # fails if it did not correctly save
    possible_file = next(load_path.glob(f"*{ROI.FILE_EXTENSION}"))
    try:
        my_roi = ROI.load(
            possible_file,
            filter_condition= lambda x : x.name == "not_test_ROI"
        )
        assert False # should fail!
    except NoROIError:
        pass

    test_ROI = ROI.load(possible_file)

    from scipy import datasets
    racoon = datasets.face().T

    assert test_ROI.name == "test_ROI"
    assert test_ROI.info_string == "test info string"
    assert test_ROI.slice_idx is None
    assert test_ROI.mask.shape == racoon.shape
    assert test_ROI.mask.dtype == bool
    assert isinstance(test_ROI, ROI)
    assert np.all(test_ROI.mask == (racoon > 100))
