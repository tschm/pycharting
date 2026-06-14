"""Tests for data ingestion and validation module."""

import numpy as np
import pandas as pd
import pytest

from pycharting.data.ingestion import DataManager, DataValidationError, validate_input


class TestValidateInput:
    """Tests for the validate_input function."""

    def test_valid_pandas_input(self):
        """Test validation with valid Pandas Series input."""
        index = pd.date_range("2024-01-01", periods=5)
        open_data = pd.Series([100, 102, 101, 103, 102])
        high = pd.Series([105, 106, 105, 107, 106])
        low = pd.Series([99, 100, 99, 101, 100])
        close = pd.Series([104, 103, 104, 105, 104])

        result = validate_input(index, open_data, high, low, close)

        assert isinstance(result["index"], np.ndarray)
        assert isinstance(result["open"], np.ndarray)
        assert len(result["index"]) == 5
        assert np.array_equal(result["open"], [100, 102, 101, 103, 102])

    def test_valid_numpy_input(self):
        """Test validation with valid NumPy array input."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        result = validate_input(index, open_data, high, low, close)

        assert isinstance(result["index"], np.ndarray)
        assert len(result["index"]) == 5
        assert np.array_equal(result["close"], [104, 103, 104, 105, 104])

    def test_with_overlays(self):
        """Test validation with overlay data."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {
            "SMA20": np.array([101, 102, 102, 103, 103]),
            "EMA10": np.array([100, 101, 101, 102, 102]),
        }

        result = validate_input(index, open_data, high, low, close, overlays=overlays)

        assert len(result["overlays"]) == 2
        assert "SMA20" in result["overlays"]
        assert "EMA10" in result["overlays"]
        assert np.array_equal(result["overlays"]["SMA20"], [101, 102, 102, 103, 103])

    def test_with_subplots(self):
        """Test validation with subplot data."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {
            "Volume": np.array([1000, 1200, 1100, 1300, 1150]),
            "RSI": np.array([55, 58, 52, 60, 57]),
        }

        result = validate_input(index, open_data, high, low, close, subplots=subplots)

        assert len(result["subplots"]) == 2
        assert "Volume" in result["subplots"]
        assert "RSI" in result["subplots"]

    def test_invalid_index_type(self):
        """Test that invalid index type raises error."""
        index = [1, 2, 3, 4, 5]  # List instead of Index or ndarray
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError, match="Index must be"):
            validate_input(index, open_data, high, low, close)

    def test_length_mismatch(self):
        """Test that mismatched lengths raise error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101])  # Length 3
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError, match="does not match index length"):
            validate_input(index, open_data, high, low, close)

    def test_ohlc_constraint_high_violation(self):
        """Test that High < max(Open, Close) raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([99, 106, 105, 107, 106])  # First high < open
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError, match="High must be >= max"):
            validate_input(index, open_data, high, low, close)

    def test_ohlc_constraint_low_violation(self):
        """Test that Low > min(Open, Close) raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([101, 100, 99, 101, 100])  # First low > open
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError, match="Low must be <= min"):
            validate_input(index, open_data, high, low, close)

    def test_overlay_length_mismatch(self):
        """Test that mismatched overlay length raises error."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {"SMA20": np.array([101, 102, 102])}  # Length 3

        with pytest.raises(DataValidationError, match=r"Overlay.*does not match"):
            validate_input(index, open_data, high, low, close, overlays=overlays)


class TestDataManager:
    """Tests for the DataManager class."""

    def test_init_with_numpy_arrays(self):
        """Test initialization with NumPy arrays."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        assert len(dm) == 5
        assert dm.length == 5
        assert isinstance(dm.open, np.ndarray)
        assert np.array_equal(dm.open, open_data)

    def test_init_with_pandas_series(self):
        """Test initialization with Pandas Series."""
        index = pd.date_range("2024-01-01", periods=5)
        open_data = pd.Series([100, 102, 101, 103, 102])
        high = pd.Series([105, 106, 105, 107, 106])
        low = pd.Series([99, 100, 99, 101, 100])
        close = pd.Series([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        assert len(dm) == 5
        assert isinstance(dm.close, np.ndarray)
        assert dm.close[0] == 104

    def test_properties(self):
        """Test all property accessors."""
        index = np.arange(3)
        open_data = np.array([100, 102, 101])
        high = np.array([105, 106, 105])
        low = np.array([99, 100, 99])
        close = np.array([104, 103, 104])

        trades = np.array([1, 0, -1])
        subplots = {"Volume": {"data": np.array([10, 20, 30]), "type": "bar"}}

        dm = DataManager(index, open_data, high, low, close, subplots=subplots, trades=trades)

        assert np.array_equal(dm.index, index)
        assert np.array_equal(dm.open, open_data)
        assert np.array_equal(dm.high, high)
        assert np.array_equal(dm.low, low)
        assert np.array_equal(dm.close, close)
        assert isinstance(dm.overlays, dict)
        assert isinstance(dm.subplots, dict)
        assert np.array_equal(dm.trades, trades)
        assert dm.subplot_meta["Volume"][0]["type"] == "bar"

    def test_with_overlays_and_subplots(self):
        """Test initialization with overlays and subplots."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        overlays = {"SMA20": np.array([101, 102, 102, 103, 103])}
        subplots = {"Volume": np.array([1000, 1200, 1100, 1300, 1150])}

        dm = DataManager(index, open_data, high, low, close, overlays, subplots)

        assert len(dm.overlays) == 1
        assert "SMA20" in dm.overlays
        assert len(dm.subplots) == 1
        assert "Volume" in dm.subplots
        assert np.array_equal(dm.overlays["SMA20"], [101, 102, 102, 103, 103])

    def test_invalid_data_raises_error(self):
        """Test that invalid OHLC data raises DataValidationError."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([99, 106, 105, 107, 106])  # First high < open
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        with pytest.raises(DataValidationError):
            DataManager(index, open_data, high, low, close)

    def test_repr(self):
        """Test string representation."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)
        repr_str = repr(dm)

        assert "DataManager" in repr_str
        assert "5 points" in repr_str

    def test_repr_with_overlays(self):
        """Test string representation with overlays."""
        index = np.arange(3)
        open_data = np.array([100, 102, 101])
        high = np.array([105, 106, 105])
        low = np.array([99, 100, 99])
        close = np.array([104, 103, 104])
        overlays = {"SMA20": np.array([101, 102, 102])}

        dm = DataManager(index, open_data, high, low, close, overlays=overlays)
        repr_str = repr(dm)

        assert "1 overlays" in repr_str

    def test_no_data_duplication(self):
        """Test that data is not duplicated unnecessarily."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Verify arrays are stored (conversion happened but data is referenced)
        assert dm.open.dtype == open_data.dtype
        assert len(dm.open) == len(open_data)

    def test_timestamp_conversion_to_milliseconds(self):
        """Test that DatetimeIndex is converted to Unix timestamps in milliseconds."""
        # Create a DatetimeIndex with known timestamps
        index = pd.date_range("2024-01-01", periods=5, freq="h")
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return timestamps in milliseconds
        chunk = dm.get_chunk(0, 5)

        # Verify that index is a list of integers (Unix timestamps in milliseconds)
        assert isinstance(chunk["index"], list)
        assert all(isinstance(x, int) for x in chunk["index"])

        # Verify timestamps are in the correct range (milliseconds since epoch)
        # For 2024-01-01, timestamps should be around 1704067200000 (ms)
        expected_first_ts = int(pd.Timestamp("2024-01-01").timestamp() * 1000)
        assert chunk["index"][0] == expected_first_ts

        # Verify timestamps are 1 hour apart (3600000 ms)
        assert chunk["index"][1] - chunk["index"][0] == 3600000

    def test_numeric_index_unchanged(self):
        """Test that numeric indices are not converted to timestamps."""
        # Use plain numeric index
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return plain numeric indices
        chunk = dm.get_chunk(0, 5)

        # Verify that index is unchanged
        assert chunk["index"] == [0, 1, 2, 3, 4]

    def test_unix_timestamp_index_unchanged(self):
        """Test that raw Unix timestamps (already in milliseconds) pass through unchanged."""
        # Use Unix timestamps in milliseconds (like JavaScript Date.now())
        base_ts = 1704067200000  # 2024-01-01 in milliseconds
        index = np.array([base_ts + i * 3600000 for i in range(5)])
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return timestamps unchanged
        chunk = dm.get_chunk(0, 5)

        # Verify timestamps are preserved
        assert chunk["index"] == index.tolist()
        assert all(isinstance(x, int) for x in chunk["index"])

    def test_timezone_aware_index(self):
        """Test that timezone-aware indices are correctly converted to milliseconds."""
        # Create a timezone-aware index (UTC)
        index = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])

        dm = DataManager(index, open_data, high, low, close)

        # Get chunk should return valid integer timestamps, NOT Timestamps objects
        chunk = dm.get_chunk(0, 5)

        # Verify conversion
        assert isinstance(chunk["index"], list)
        assert all(isinstance(x, int) for x in chunk["index"])

        # Expected timestamp (1704067200000 for 2024-01-01 UTC)
        expected_ts = 1704067200000
        assert chunk["index"][0] == expected_ts


class TestValidateInputEdgeCases:
    """Tests for edge cases in validate_input."""

    def test_to_array_none_returns_none(self):
        """Verify omitted data series default to None in the result."""
        index = np.arange(5)
        close = np.array([100, 102, 103, 104, 105])
        result = validate_input(index, close=close)
        assert result["open"] is None
        assert result["high"] is None
        assert result["low"] is None

    def test_to_array_list_input(self):
        """Verify plain Python lists are converted to numpy arrays."""
        index = np.arange(5)
        result = validate_input(
            index,
            [100, 102, 101, 103, 102],
            [105, 106, 105, 107, 106],
            [99, 100, 99, 101, 100],
            [104, 103, 104, 105, 104],
        )
        assert isinstance(result["open"], np.ndarray)
        assert np.array_equal(result["open"], [100, 102, 101, 103, 102])

    def test_to_array_invalid_type_raises(self):
        """Verify passing a non-array-like type as a data series raises an error."""
        index = np.arange(5)
        with pytest.raises(DataValidationError):
            validate_input(index, "invalid", np.zeros(5), np.zeros(5), np.zeros(5))

    def test_no_series_raises(self):
        """Verify calling validate_input with no data series raises an error."""
        index = np.arange(5)
        with pytest.raises(DataValidationError, match="At least one data series"):
            validate_input(index)

    def test_single_series_mode(self):
        """Verify passing only close yields a single-series result with other fields None."""
        index = np.arange(5)
        close = np.array([100, 102, 103, 104, 105])
        result = validate_input(index, close=close)
        assert result["open"] is None
        assert result["high"] is None
        assert result["low"] is None
        assert np.array_equal(result["close"], close)

    def test_open_fallback_when_none(self):
        """Verify open falls back to close when open is None."""
        index = np.arange(5)
        high = np.array([106, 108, 107, 109, 108])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        result = validate_input(index, None, high, low, close)
        assert np.array_equal(result["open"], close)

    def test_close_fallback_when_none(self):
        """Verify close falls back to open when close is None."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        result = validate_input(index, open_data, high, low, None)
        assert np.array_equal(result["close"], open_data)

    def test_open_close_fallback_when_both_none(self):
        """When neither open nor close is given, both fall back to the first provided series."""
        index = np.arange(5)
        high = np.array([106, 108, 107, 109, 108])
        low = np.array([99, 100, 99, 101, 100])
        result = validate_input(index, None, high, low, None)
        # high is the first provided series, so open and close both default to it.
        assert np.array_equal(result["open"], high)
        assert np.array_equal(result["close"], high)

    def test_high_auto_computed(self):
        """Verify high is auto-computed as the element-wise maximum of open and close."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        close = np.array([104, 101, 104, 102, 105])
        result = validate_input(index, open_data, None, None, close)
        assert np.array_equal(result["high"], np.maximum(open_data, close))

    def test_low_auto_computed(self):
        """Verify low is auto-computed as the element-wise minimum of open and close."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        close = np.array([104, 101, 104, 102, 105])
        result = validate_input(index, open_data, None, None, close)
        assert np.array_equal(result["low"], np.minimum(open_data, close))

    def test_trades_valid(self):
        """Verify a valid trades array is accepted and cast to int8."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        trades = np.array([1, 0, -1, 0, 1])
        result = validate_input(index, open_data, high, low, close, trades=trades)
        assert result["trades"] is not None
        assert result["trades"].dtype == np.int8

    def test_trades_invalid_values_raise(self):
        """Verify a trades array with values outside -1, 0, 1 raises an error."""
        index = np.arange(5)
        close = np.array([100, 102, 103, 104, 105])
        with pytest.raises(DataValidationError, match="Trades array must contain only"):
            validate_input(index, close=close, trades=np.array([1, 2, -1, 0, 1]))

    def test_subplot_multi_series_format(self):
        """Verify a list of subplot series is split into indexed keys with metadata."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {
            "MACD": [
                {"data": np.array([1.0, 1.5, 2.0, 1.5, 1.0]), "type": "line", "label": "MACD", "color": "#f00"},
                {"data": np.array([0.5, 0.8, 1.0, 0.7, 0.5]), "type": "bar"},
            ]
        }
        result = validate_input(index, open_data, high, low, close, subplots=subplots)
        assert "MACD__0" in result["subplots"]
        assert "MACD__1" in result["subplots"]
        assert len(result["subplot_meta"]["MACD"]) == 2

    def test_subplot_dict_format(self):
        """Verify a single-dict subplot definition is parsed with its type metadata."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {"Volume": {"data": np.array([1000, 1200, 800, 1500, 1100]), "type": "bar", "color": "#0f0"}}
        result = validate_input(index, open_data, high, low, close, subplots=subplots)
        assert "Volume" in result["subplots"]
        assert result["subplot_meta"]["Volume"][0]["type"] == "bar"


class TestDataManagerEdgeCases:
    """Tests for DataManager repr and chunk edge cases."""

    def test_repr_with_subplots(self):
        """Verify the DataManager repr reports the number of subplots."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {"RSI": np.array([55, 58, 52, 60, 57])}
        dm = DataManager(index, open_data, high, low, close, subplots=subplots)
        assert "1 subplots" in repr(dm)

    def test_get_chunk_includes_subplot_meta(self):
        """Verify get_chunk includes subplot_meta with subplot keys in the result."""
        index = np.arange(5)
        open_data = np.array([100, 102, 101, 103, 102])
        high = np.array([105, 106, 105, 107, 106])
        low = np.array([99, 100, 99, 101, 100])
        close = np.array([104, 103, 104, 105, 104])
        subplots = {"Volume": np.array([1000, 1200, 1100, 1300, 1150])}
        dm = DataManager(index, open_data, high, low, close, subplots=subplots)
        chunk = dm.get_chunk(0, 5)
        assert "subplot_meta" in chunk
        assert "Volume" in chunk["subplot_meta"]
