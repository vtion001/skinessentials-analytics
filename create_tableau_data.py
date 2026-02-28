#!/usr/bin/env python3
"""
Create Tableau Workbook from Analytics Data
Creates a .twbx file that can be published to Tableau
"""

import json
import csv
import os
import tempfile
import zipfile
from pathlib import Path

# Read the analytics data
data_file = "data_report_www.skinessentialsbyher.com_20260226.json"

with open(data_file) as f:
    data = json.load(f)

channels = data.get("channels", {})
gsc = channels.get("gsc", {})
ga4 = channels.get("ga4", {})
meta = channels.get("meta", {})
scores = data.get("scores", {})

# Create CSV files for different data sources
output_dir = Path("tableau_data")
output_dir.mkdir(exist_ok=True)

# 1. Executive Summary CSV
with open(output_dir / "executive_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value", "Score"])
    writer.writerow(
        ["Overall Score", scores.get("overall", 0), scores.get("overall", 0)]
    )
    writer.writerow(
        [
            "Search Visibility",
            scores.get("search_visibility", 0),
            scores.get("search_visibility", 0),
        ]
    )
    writer.writerow(
        [
            "GA4 Performance",
            scores.get("ga4_performance", 0),
            scores.get("ga4_performance", 0),
        ]
    )
    writer.writerow(
        [
            "Meta Performance",
            scores.get("meta_performance", 0),
            scores.get("meta_performance", 0),
        ]
    )

# 2. Search Performance CSV
with open(output_dir / "search_performance.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Clicks", gsc.get("total_clicks", 0)])
    writer.writerow(["Total Impressions", gsc.get("total_impressions", 0)])
    writer.writerow(["Average CTR", gsc.get("average_ctr", 0)])
    writer.writerow(["Average Position", gsc.get("average_position", 0)])

# 3. Top Queries CSV
with open(output_dir / "top_queries.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Query", "Clicks", "Impressions", "CTR", "Position"])
    for q in gsc.get("top_queries", [])[:20]:
        keys = q.get("keys", [""])
        writer.writerow(
            [
                keys[0] if keys else "",
                q.get("clicks", 0),
                q.get("impressions", 0),
                q.get("ctr", 0),
                q.get("position", 0),
            ]
        )

# 4. Web Analytics CSV
with open(output_dir / "web_analytics.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Sessions", ga4.get("total_sessions", 0)])
    writer.writerow(["Users", ga4.get("total_users", 0)])
    writer.writerow(["Bounce Rate", ga4.get("bounce_rate", 0)])
    writer.writerow(["Conversions", ga4.get("conversions", 0)])

# 5. Device Breakdown CSV
with open(output_dir / "device_breakdown.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Device", "Sessions"])
    for device, count in ga4.get("device_breakdown", {}).items():
        writer.writerow([device, count])

# 6. Events CSV
events = ga4.get("events", {})
if events:
    with open(output_dir / "events.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "Count", "Sessions", "Users"])
        for e in events.get("top_events", []):
            writer.writerow(
                [
                    e.get("name", ""),
                    e.get("count", 0),
                    e.get("sessions", 0),
                    e.get("users", 0),
                ]
            )

# 7. Social Media CSV
with open(output_dir / "social_media.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Impressions", meta.get("total_impressions", 0)])
    writer.writerow(["Engaged Users", meta.get("total_engaged_users", 0)])
    writer.writerow(["Page Fans", meta.get("total_fans", 0)])
    writer.writerow(["Engagement Rate", meta.get("engagement_rate", 0)])

print("✅ Created Tableau data files:")
for f in output_dir.glob("*.csv"):
    print(f"   - {f.name}")

# Create a simple TWB template (Tableau Workbook XML)
twb_content = f"""<?xml version='1.1' encoding='utf-8' ?>

<workbook xmlns="http://tableau.com/workbook" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://tableau.com/workbook http://tableau.com/xml/schema-3-3-0.xsd" version="3.3" source-build="2024.1 (20241.24.0403.1636)">
  <worksheets>
    <worksheet name="Executive Summary">
      <table>
        <view>
          <datasources>
            <datasource caption='Executive Summary' name='federated.abc123'>
              <connection class='excel-direct' filename='executive_summary.csv' />
            </datasource>
          </datasheets>
        </view>
      </table>
    </worksheet>
  </worksheets>
</workbook>
"""

print("\n📊 Data files ready for Tableau!")
print("\nTo create a dashboard in Tableau:")
print("1. Open Tableau Desktop")
print("2. Connect to the CSV files in 'tableau_data/' folder")
print("3. Create visualizations")
print("4. Publish to Tableau Cloud")

# Copy files to Desktop
import shutil

desktop_dir = (
    Path.home()
    / "Desktop"
    / "data-analyst"
    / "skinessentialsbyher.com-reports"
    / "tableau_data"
)
desktop_dir.mkdir(parents=True, exist_ok=True)

for f in output_dir.glob("*.csv"):
    shutil.copy(f, desktop_dir / f.name)

print(f"\n📁 Also copied to: {desktop_dir}")
