"""
Tests for reporting queries, dashboard statistics aggregation, and CSV exports.
"""
import csv
from pathlib import Path
import tempfile
from app.services import report_service


def test_dashboard_statistics(temp_db):
    """Verify aggregated dashboard statistics return non-zero metrics from seed data."""
    stats = report_service.get_dashboard_summary()
    assert stats["active_buses"] >= 8
    assert stats["active_routes"] >= 10
    assert stats["total_confirmed_bookings"] > 0
    assert stats["total_revenue"] > 0
    assert len(stats["recent_bookings"]) > 0


def test_csv_report_export(temp_db):
    """Test generating a report and exporting it to CSV."""
    headers, rows = report_service.get_report("confirmed_bookings")
    assert len(headers) > 0
    assert len(rows) > 0

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        out_csv = tf.name

    try:
        exported_path = report_service.export_report_to_csv(headers, rows, out_csv)
        assert Path(exported_path).exists()

        # Read back CSV and verify headers and rows
        with open(exported_path, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            assert reader[0] == headers
            assert len(reader) == len(rows) + 1
    finally:
        try:
            Path(out_csv).unlink()
        except Exception:
            pass
