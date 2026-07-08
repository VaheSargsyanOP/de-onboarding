import pytest

from etl.quality.check_silver import evaluate_quality


def test_evaluate_quality_passes_with_all_zero():
    # Should not raise.
    evaluate_quality(row_count=100, null_count=0, duplicate_count=0, invalid_temperature_count=0)


def test_evaluate_quality_fails_on_empty_table():
    with pytest.raises(RuntimeError, match="Silver table is empty"):
        evaluate_quality(row_count=0, null_count=0, duplicate_count=0, invalid_temperature_count=0)


def test_evaluate_quality_fails_on_nulls():
    with pytest.raises(RuntimeError, match="NULL values"):
        evaluate_quality(row_count=10, null_count=2, duplicate_count=0, invalid_temperature_count=0)


def test_evaluate_quality_fails_on_duplicates():
    with pytest.raises(RuntimeError, match="duplicate business keys"):
        evaluate_quality(row_count=10, null_count=0, duplicate_count=1, invalid_temperature_count=0)


def test_evaluate_quality_fails_on_invalid_temperature():
    with pytest.raises(RuntimeError, match="invalid temperatures"):
        evaluate_quality(row_count=10, null_count=0, duplicate_count=0, invalid_temperature_count=3)


def test_evaluate_quality_checks_row_count_before_other_checks():
    # Empty-table check should win even if other counts would also fail,
    # matching the original script's check ordering.
    with pytest.raises(RuntimeError, match="Silver table is empty"):
        evaluate_quality(row_count=0, null_count=5, duplicate_count=5, invalid_temperature_count=5)
