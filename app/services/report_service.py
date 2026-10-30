"""
Report service for generating analytics and exporting reports to CSV.
"""
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.repositories import report_repository


def get_dashboard_summary() -> Dict[str, Any]:
    return report_repository.get_dashboard_stats()


def get_report(report_type: str) -> Tuple[List[str], List[List[Any]]]:
    """Retrieves headers and table rows for the specified report type."""
    if report_type == "confirmed_bookings":
        return report_repository.report_all_confirmed_bookings()
    elif report_type == "cancelled_bookings":
        return report_repository.report_cancelled_bookings()
    elif report_type == "bookings_by_route":
        return report_repository.report_bookings_by_route()
    elif report_type == "bookings_by_bus":
        return report_repository.report_bookings_by_bus()
    elif report_type == "bus_occupancy":
        return report_repository.report_bus_occupancy()
    else:
        raise ValueError(f"Unknown report type: {report_type}")


def export_report_to_csv(headers: List[str], rows: List[List[Any]], output_filepath: str) -> str:
    """
    Exports report headers and row records to a CSV file.
    Returns the absolute path of the generated CSV file.
    """
    dest_path = Path(output_filepath)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(rows)

    return str(dest_path.resolve())
