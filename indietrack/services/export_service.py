import io
import csv
from datetime import datetime, timezone


def sanitize_csv_cell(value) -> str:
    """
    Sanitizes cell contents against Spreadsheet Formula Injection (CSV Injection / CWE-1236).
    If a string starts with =, +, -, @, tab, or carriage return, prefixes with an apostrophe.
    """
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


class ExportService:
    """Service generating secure, formula-safe CSV reports."""

    @classmethod
    def generate_campaign_csv_report(cls, metrics_data: list, artist_name: str) -> str:
        """
        Generates a formula-safe CSV string containing campaign metrics.
        metrics_data: list of dicts or tuples containing campaign and metric records.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header metadata block
        utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        writer.writerow([sanitize_csv_cell("IndieTrack Analytics Report")])
        writer.writerow([sanitize_csv_cell(f"Artist: {artist_name}")])
        writer.writerow([sanitize_csv_cell(f"Export Generated: {utc_now}")])
        writer.writerow([sanitize_csv_cell("NOTICE: Columns clearly indicate data_source (manual_entry vs sample_data)")])
        writer.writerow([])  # Blank row

        # Table columns
        headers = [
            "Metric ID",
            "Date",
            "Song Title",
            "Campaign Name",
            "Platform",
            "Impressions",
            "Clicks",
            "Engagement",
            "Reported Streams",
            "Spend (USD)",
            "CTR (%)",
            "CPC (USD)",
            "Data Source",
            "Notes"
        ]
        writer.writerow([sanitize_csv_cell(h) for h in headers])

        total_imps = 0
        total_clicks = 0
        total_eng = 0
        total_streams = 0
        total_spend = 0.0

        for row in metrics_data:
            imps = row.get("impressions", 0)
            clicks = row.get("clicks", 0)
            eng = row.get("engagement", 0)
            streams = row.get("reported_streams", 0)
            spend = float(row.get("spend", 0.0))

            total_imps += imps
            total_clicks += clicks
            total_eng += eng
            total_streams += streams
            total_spend += spend

            ctr = round((clicks / imps) * 100.0, 2) if imps > 0 else 0.00
            cpc = round(spend / clicks, 2) if clicks > 0 else 0.00

            writer.writerow([
                sanitize_csv_cell(row.get("metric_id", "")),
                sanitize_csv_cell(row.get("metric_date", "")),
                sanitize_csv_cell(row.get("song_title", "")),
                sanitize_csv_cell(row.get("campaign_name", "")),
                sanitize_csv_cell(row.get("platform", "")),
                sanitize_csv_cell(imps),
                sanitize_csv_cell(clicks),
                sanitize_csv_cell(eng),
                sanitize_csv_cell(streams),
                sanitize_csv_cell(f"{spend:.2f}"),
                sanitize_csv_cell(f"{ctr:.2f}%"),
                sanitize_csv_cell(f"${cpc:.2f}"),
                sanitize_csv_cell(row.get("data_source", "manual_entry")),
                sanitize_csv_cell(row.get("notes", ""))
            ])

        # Summary Row
        overall_ctr = round((total_clicks / total_imps) * 100.0, 2) if total_imps > 0 else 0.00
        overall_cpc = round(total_spend / total_clicks, 2) if total_clicks > 0 else 0.00

        writer.writerow([])
        writer.writerow([
            sanitize_csv_cell("TOTALS / AVERAGES"),
            "",
            "",
            "",
            "",
            sanitize_csv_cell(total_imps),
            sanitize_csv_cell(total_clicks),
            sanitize_csv_cell(total_eng),
            sanitize_csv_cell(total_streams),
            sanitize_csv_cell(f"{total_spend:.2f}"),
            sanitize_csv_cell(f"{overall_ctr:.2f}%"),
            sanitize_csv_cell(f"${overall_cpc:.2f}"),
            sanitize_csv_cell("AGGREGATED"),
            ""
        ])

        return output.getvalue()
