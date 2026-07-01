import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'code', 'phase-2-training'))

from predict import CDTPredictor


@pytest.fixture(scope="module")
def predictor():
    return CDTPredictor()


def test_predictor_initializes(predictor):
    assert predictor is not None
    assert hasattr(predictor, 'predict')
    assert hasattr(predictor, 'monte_carlo')


def test_basic_prediction(predictor):
    w48 = np.zeros(48, dtype=np.float32)
    w48[0:12] = 25.0
    w48[12:24] = 28.0
    w48[24:36] = 75.0
    w48[36:48] = 0.6
    result = predictor.predict(w48, "Ganjam", "Kharif", 2024)
    assert "predicted_yield" in result
    assert "failure_probability" in result
    assert result["predicted_yield"] > 0
    assert 0 <= result["failure_probability"] <= 1


def test_monte_carlo(predictor):
    w48 = np.zeros(48, dtype=np.float32)
    w48[0:12] = 25.0
    w48[12:24] = 28.0
    w48[24:36] = 75.0
    w48[36:48] = 0.6
    result = predictor.monte_carlo(w48, "Ganjam", "Kharif", 2024, n_samples=20)
    assert "monte_carlo_distribution" in result
    assert "predicted_yield" in result
    assert "monte_carlo_std" in result
    assert "confidence_interval" in result
    assert len(result["monte_carlo_distribution"]) == 20
    assert result["predicted_yield"] > 0


@pytest.mark.parametrize("district", ["Angul", "Cuttack", "Kandhamal", "Koraput", "Sundargarh"])
def test_multiple_districts(predictor, district):
    w48 = np.zeros(48, dtype=np.float32)
    w48[0:12] = 20.0
    w48[12:24] = 27.0
    w48[24:36] = 80.0
    w48[36:48] = 0.5
    result = predictor.predict(w48, district, "Kharif", 2024)
    assert result["predicted_yield"] > 0
    assert 0 <= result["failure_probability"] <= 1


def test_rabi_season(predictor):
    w48 = np.ones(48, dtype=np.float32) * 0.3
    w48[0:12] = 5.0
    w48[12:24] = 22.0
    w48[24:36] = 65.0
    w48[36:48] = 0.7
    result = predictor.predict(w48, "Ganjam", "Rabi", 2024)
    assert result["predicted_yield"] > 0


def test_unknown_district(predictor):
    w48 = np.zeros(48, dtype=np.float32)
    with pytest.raises(ValueError, match="Unknown district"):
        predictor.predict(w48, "Faketrict", "Kharif", 2024)


def test_attention_weights_shape(predictor):
    w48 = np.zeros(48, dtype=np.float32)
    w48[0:12] = 25.0
    w48[12:24] = 28.0
    w48[24:36] = 75.0
    w48[36:48] = 0.6
    result = predictor.predict(w48, "Ganjam", "Kharif", 2024)
    assert "attention_weights" in result
    assert len(result["attention_weights"]) == 84


def test_stacked_vs_single(predictor):
    w48_normal = np.zeros(48, dtype=np.float32)
    w48_normal[0:12] = 30.0
    w48_normal[12:24] = 28.0
    w48_normal[24:36] = 75.0
    w48_normal[36:48] = 0.5

    w48_drought = w48_normal.copy()
    w48_drought[0:12] = 5.0
    w48_drought[36:48] = 0.2

    normal = predictor.predict(w48_normal, "Ganjam", "Kharif", 2024)
    drought = predictor.predict(w48_drought, "Ganjam", "Kharif", 2024)
    assert drought["predicted_yield"] < normal["predicted_yield"]
    assert drought["failure_probability"] >= normal["failure_probability"]
