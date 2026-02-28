"""
Data Analyst Agent

 multi-channel data analysisA comprehensive agent for combining:
- Google Search Console (SEO performance)
- Google Analytics 4 (web analytics)
- Meta/Facebook Insights (social media performance)
- Historical tracking & trend analysis
- Growth-driven recommendations

Usage:
    python data_analyst.py <website_url> [--days 30] [--channels gsc,ga4,meta]
    python data_analyst.py --schedule daily    # Run daily analysis
    python data_analyst.py --schedule weekly   # Run weekly analysis

Author: Data Intelligence Agent
Version: 2.0.0
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


class DataAnalyst:
    """
    Multi-Channel Data Analyst Agent

    Integrates:
    - Google Search Console (SEO/Search)
    - Google Analytics 4 (Web Analytics)
    - Meta/Facebook Insights (Social)
    """

    def __init__(self, credentials_path: Optional[str] = None):
        # Resolve credentials path relative to the data_analyst.py file location
        base_dir = Path(__file__).parent
        env_creds = os.getenv("GSC_CREDENTIALS_PATH")

        if credentials_path:
            self.credentials_path = (
                str(base_dir / credentials_path)
                if not Path(credentials_path).is_absolute()
                else credentials_path
            )
        elif env_creds:
            self.credentials_path = (
                str(base_dir / env_creds)
                if not Path(env_creds).is_absolute()
                else env_creds
            )
        else:
            self.credentials_path = str(base_dir / "service-account.json")

        self.gsc_service = None
        self.site_url = None

        self.ga4_property_id = os.getenv("GA4_PROPERTY_ID")

        env_ga4_creds = os.getenv("GA4_CREDENTIALS_PATH")
        if env_ga4_creds:
            self.ga4_credentials_path = (
                str(base_dir / env_ga4_creds)
                if not Path(env_ga4_creds).is_absolute()
                else env_ga4_creds
            )
        else:
            self.ga4_credentials_path = self.credentials_path

        self.meta_access_token = os.getenv("META_ACCESS_TOKEN")
        self.meta_app_id = os.getenv("META_APP_ID")
        self.meta_page_id = os.getenv("META_PAGE_ID")

        # OpenRouter AI for comprehensive insights
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        self.performance_data = {}
        self.ga4_data = {}
        self.meta_data = {}

        self.weights = {
            "search_visibility": 0.20,
            "ga4_performance": 0.30,
            "meta_performance": 0.20,
            "technical_health": 0.15,
            "content_performance": 0.15,
        }

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DataAnalystAgent/2.0"})

        # Historical data storage
        self.data_dir = Path(__file__).parent / "history"
        self.data_dir.mkdir(exist_ok=True)

        # Default author for reports
        self.author_name = "Vincent John Rodriguez"

        print("📊 Data Analyst Agent v2.0 initialized")

    def load_historical_data(self, site_url: str) -> List[Dict]:
        """Load historical report data"""
        site_name = (
            site_url.replace("https://", "").replace("http://", "").replace("www.", "")
        )
        history_file = self.data_dir / f"history_{site_name}.json"

        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_historical_data(self, site_url: str, report: Dict) -> None:
        """Save report to historical data"""
        site_name = (
            site_url.replace("https://", "").replace("http://", "").replace("www.", "")
        )
        history_file = self.data_dir / f"history_{site_name}.json"

        history = self.load_historical_data(site_url)
        history.append({"date": datetime.now().isoformat(), "report": report})

        # Keep only last 90 days of data
        cutoff = datetime.now() - timedelta(days=90)
        history = [h for h in history if datetime.fromisoformat(h["date"]) > cutoff]

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def analyze_trends(self, site_url: str) -> Dict[str, Any]:
        """Analyze trends from historical data"""
        history = self.load_historical_data(site_url)

        if len(history) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 reports for trend analysis",
            }

        # Get last 2 reports
        current = history[-1]["report"]
        previous = history[-2]["report"]

        trends = {}

        # GSC Trends
        current_gsc = current.get("channels", {}).get("gsc", {})
        previous_gsc = previous.get("channels", {}).get("gsc", {})

        if current_gsc and previous_gsc:
            gsc_trends = self._calculate_trend(
                current_gsc.get("total_clicks", 0), previous_gsc.get("total_clicks", 0)
            )
            gsc_trends["position_change"] = previous_gsc.get(
                "average_position", 0
            ) - current_gsc.get("average_position", 0)
            trends["gsc"] = gsc_trends

        # GA4 Trends
        current_ga4 = current.get("channels", {}).get("ga4", {})
        previous_ga4 = previous.get("channels", {}).get("ga4", {})

        if current_ga4 and previous_ga4:
            trends["ga4"] = {
                "sessions_change": self._calculate_trend(
                    current_ga4.get("total_sessions", 0),
                    previous_ga4.get("total_sessions", 0),
                ),
                "bounce_rate_change": (
                    previous_ga4.get("bounce_rate", 0)
                    - current_ga4.get("bounce_rate", 0)
                ),
                "conversions_change": self._calculate_trend(
                    current_ga4.get("conversions", 0),
                    previous_ga4.get("conversions", 0),
                ),
            }

        # Meta Trends
        current_meta = current.get("channels", {}).get("meta", {})
        previous_meta = previous.get("channels", {}).get("meta", {})

        if current_meta and previous_meta:
            trends["meta"] = {
                "impressions_change": self._calculate_trend(
                    current_meta.get("total_impressions", 0),
                    previous_meta.get("total_impressions", 0),
                ),
                "engagement_change": self._calculate_trend(
                    current_meta.get("engagement_rate", 0),
                    previous_meta.get("engagement_rate", 0),
                ),
            }

        # Overall trend
        current_score = current.get("overall_score", 0)
        previous_score = previous.get("overall_score", 0)
        trends["overall"] = {
            "score_change": current_score - previous_score,
            "direction": "up"
            if current_score > previous_score
            else "down"
            if current_score < previous_score
            else "stable",
        }

        return trends

    def _calculate_trend(self, current: float, previous: float) -> Dict[str, Any]:
        """Calculate percentage change"""
        if previous == 0:
            return {
                "current": current,
                "previous": previous,
                "change_pct": 0,
                "direction": "new",
            }

        change = current - previous
        change_pct = (change / previous) * 100

        return {
            "current": current,
            "previous": previous,
            "change": change,
            "change_pct": round(change_pct, 1),
            "direction": "up" if change > 0 else "down" if change < 0 else "stable",
        }

    def generate_growth_recommendations(
        self, site_url: str, trends: Dict
    ) -> List[Dict]:
        """Generate growth-driven recommendations based on trends"""
        recommendations = []
        history = self.load_historical_data(site_url)

        if not history:
            return self._get_default_recommendations()

        current = history[-1]["report"]
        gsc = current.get("channels", {}).get("gsc", {})
        ga4 = current.get("channels", {}).get("ga4", {})
        meta = current.get("channels", {}).get("meta", {})

        # Analyze trends and generate specific recommendations
        if trends.get("gsc"):
            gsc_trend = trends["gsc"]
            if gsc_trend.get("direction") == "down":
                recommendations.append(
                    {
                        "priority": "Critical",
                        "category": "SEO",
                        "title": "📉 Search Traffic Declining",
                        "description": f"Clicks are down {abs(gsc_trend.get('change_pct', 0))}% from last period. Immediate action needed.",
                        "action": "Review recent algorithm changes, check for technical issues, and audit backlink profile.",
                        "impact": "High",
                        "timeline": "This week",
                    }
                )
            elif gsc_trend.get("position_change", 0) > 0:
                recommendations.append(
                    {
                        "priority": "Growth",
                        "category": "SEO",
                        "title": "📈 Rankings Improving",
                        "description": f"Average position improved by {gsc_trend.get('position_change', 0):.1f} positions. Capitalize on this momentum!",
                        "action": "Create more content around top-performing keywords and build backlinks.",
                        "impact": "High",
                        "timeline": "Next 2 weeks",
                    }
                )

        if trends.get("ga4"):
            ga4_trend = trends["ga4"]
            if ga4_trend.get("bounce_rate_change", 0) < -0.05:
                recommendations.append(
                    {
                        "priority": "Critical",
                        "category": "UX",
                        "title": "⚠️ Bounce Rate Increasing",
                        "description": f"Bounce rate increased. Users are leaving without engaging.",
                        "action": "Improve page load speed, enhance content quality, add clear CTAs.",
                        "impact": "High",
                        "timeline": "This week",
                    }
                )
            if ga4_trend.get("conversions_change", {}).get("direction") == "up":
                recommendations.append(
                    {
                        "priority": "Growth",
                        "category": "Conversion",
                        "title": "🎯 Conversions Growing",
                        "description": "Your conversion optimization is working! Scale what's working.",
                        "action": "Double down on high-converting pages and traffic sources.",
                        "impact": "High",
                        "timeline": "Immediately",
                    }
                )

        if trends.get("meta"):
            meta_trend = trends["meta"]
            if meta_trend.get("impressions_change", {}).get("direction") == "up":
                imp = meta_trend["impressions_change"]
                recommendations.append(
                    {
                        "priority": "Growth",
                        "category": "Social",
                        "title": "🚀 Social Reach Growing",
                        "description": f"Impressions up {imp.get('change_pct', 0)}%! Leverage this reach.",
                        "action": "Increase posting frequency and test paid promotion to scale.",
                        "impact": "Medium",
                        "timeline": "This week",
                    }
                )

        # Add current performance recommendations
        if ga4.get("bounce_rate", 0) > 0.6:
            recommendations.append(
                {
                    "priority": "High",
                    "category": "UX",
                    "title": "🔴 High Bounce Rate",
                    "description": f"{ga4.get('bounce_rate', 0):.0%} bounce rate is hurting conversions.",
                    "action": "Audit top landing pages, improve mobile experience, add engaging content.",
                    "impact": "High",
                    "timeline": "This week",
                }
            )

        if gsc.get("average_position", 0) > 5:
            recommendations.append(
                {
                    "priority": "High",
                    "category": "SEO",
                    "title": "🎯 Position 5-10 Opportunity",
                    "description": f"Average ranking at {gsc.get('average_position', 0):.1f}. Small improvements = big traffic gains.",
                    "action": "Optimize content for top 10 keywords, build 2-3 quality backlinks.",
                    "impact": "High",
                    "timeline": "2-4 weeks",
                }
            )

        if meta.get("engagement_rate", 0) < 0.03:
            recommendations.append(
                {
                    "priority": "Medium",
                    "category": "Social",
                    "title": "📱 Low Engagement",
                    "description": f"Only {meta.get('engagement_rate', 0):.1%} engagement. Content may not be resonating.",
                    "action": "Test video content, ask questions, share customer stories.",
                    "impact": "Medium",
                    "timeline": "This week",
                }
            )

        # Add growth opportunities
        recommendations.extend(
            [
                {
                    "priority": "Growth",
                    "category": "Content",
                    "title": "📝 Content Gap Analysis",
                    "description": "Identify content opportunities your competitors rank for but you don't.",
                    "action": "Use GSC to find keywords with impressions but no clicks - these are opportunities.",
                    "impact": "Medium",
                    "timeline": "This month",
                },
                {
                    "priority": "Growth",
                    "category": "Traffic",
                    "title": "🔗 Referral Traffic Strategy",
                    "description": "Build strategic partnerships for referral traffic.",
                    "action": "Guest post, collaborations, directory submissions.",
                    "impact": "Medium",
                    "timeline": "This month",
                },
            ]
        )

        return recommendations[:8]

    def _get_default_recommendations(self) -> List[Dict]:
        """Get default recommendations for new accounts"""
        return [
            {
                "priority": "High",
                "category": "Setup",
                "title": "🔧 Complete GA4 Setup",
                "description": "Set up conversion events in GA4 to track business goals.",
                "action": "Configure at least 3 conversion events (signups, purchases, contact forms).",
                "impact": "High",
                "timeline": "This week",
            },
            {
                "priority": "High",
                "category": "SEO",
                "title": "🎯 Keyword Research",
                "description": "Identify your top 10 target keywords with good search volume.",
                "action": "Use GSC data to find keywords where you rank 5-15 - optimize these pages.",
                "impact": "High",
                "timeline": "This week",
            },
            {
                "priority": "Medium",
                "category": "Social",
                "title": "📱 Content Calendar",
                "description": "Create a consistent posting schedule.",
                "action": "Post 5x per week: 2 educational, 1 behind-scenes, 1 customer story, 1 promotional.",
                "impact": "Medium",
                "timeline": "Ongoing",
            },
        ]

    def run_scheduled_analysis(self, site_url: str, schedule: str = "daily") -> None:
        """Run scheduled analysis"""
        if schedule == "daily":
            days = 1
        elif schedule == "weekly":
            days = 7
        else:
            days = 30

        print(f"\n{'=' * 60}")
        print(f"🔄 SCHEDULED ANALYSIS: {schedule.upper()}")
        print(f"{'=' * 60}")

        analyst = DataAnalyst()
        analyst.authenticate_gsc()
        analyst.authenticate_ga4()
        analyst.authenticate_meta()

        analyst.set_site(site_url)
        report = analyst.generate_unified_report(site_url, days, ["gsc", "ga4", "meta"])

        if report:
            # Save historical data
            analyst.save_historical_data(site_url, report)

            # Generate and save report
            site_name = (
                site_url.replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
            )
            output_file = f"data_report_{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            analyst.export_report(report, output_file)

            # Analyze trends
            trends = analyst.analyze_trends(site_url)

            # Generate growth recommendations
            recommendations = analyst.generate_growth_recommendations(site_url, trends)

            # Generate dashboard
            dashboard_file = (
                f"dashboard_{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            )
            analyst.export_streamlit_dashboard(
                report, dashboard_file, trends, recommendations
            )

            # Print summary
            print(f"\n📊 SCHEDULED ANALYSIS COMPLETE")
            print(f"   Site: {site_url}")
            print(f"   Period: Last {days} days")
            print(f"   Overall Score: {report.get('overall_score', 0):.1f}/100")

            if trends.get("overall"):
                t = trends["overall"]
                print(
                    f"   Trend: {t.get('direction', 'stable').upper()} ({t.get('score_change', 0):+.1f} points)"
                )

            print(f"\n📈 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(
                    f"   {i}. [{rec.get('priority', 'Medium')}] {rec.get('title', '')}"
                )

            # Open dashboard
            print("\n🚀 Opening dashboard...")
            subprocess.Popen(
                ["streamlit", "run", dashboard_file, "--server.headless", "false"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

    def authenticate_gsc(self, credentials_path: Optional[str] = None) -> bool:
        """Authenticate with Google Search Console"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_path = credentials_path or self.credentials_path

            if not creds_path or not os.path.exists(creds_path):
                print(f"⚠️  GSC: Credentials file not found: {creds_path}")
                return False

            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )

            self.gsc_service = build("webmasters", "v3", credentials=credentials)
            print("✅ GSC: Authenticated with Google Search Console API")
            return True

        except ImportError:
            print("⚠️  GSC: google-auth libraries not installed")
            return False
        except Exception as e:
            print(f"⚠️  GSC: Authentication failed - {e}")
            return False

    def authenticate_ga4(self) -> bool:
        """Authenticate with Google Analytics 4 Data API"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_path = self.ga4_credentials_path

            if not creds_path or not os.path.exists(creds_path):
                print(f"⚠️  GA4: Credentials file not found: {creds_path}")
                return False

            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )

            self.ga4_service = build("analyticsdata", "v1beta", credentials=credentials)
            print("✅ GA4: Authenticated with Google Analytics Data API")
            return True

        except ImportError:
            print("⚠️  GA4: google-analytics-data not installed")
            print(
                "   Install: pip3 install --break-system-packages google-analytics-data"
            )
            return False
        except Exception as e:
            print(f"⚠️  GA4: Authentication failed - {e}")
            return False

    def authenticate_meta(self) -> bool:
        """Validate Meta/Facebook access token"""
        if not self.meta_access_token:
            print("⚠️  Meta: No access token. Running in demo mode.")
            return False

        try:
            debug_url = "https://graph.facebook.com/v21.0/debug_token"
            params = {
                "input_token": self.meta_access_token,
                "access_token": self.meta_access_token,
            }
            response = self.session.get(debug_url, params=params, timeout=10)
            data = response.json()

            if data.get("data", {}).get("is_valid"):
                print(f"✅ Meta: Access token validated")
                print(f"   App ID: {data['data'].get('app_id')}")
                print(f"   Scopes: {data['data'].get('scopes', [])}")
                return True
            else:
                print(f"⚠️  Meta: Invalid access token")
                return False

        except Exception as e:
            print(f"⚠️  Meta: Token validation failed - {e}")
            return False

    def set_site(self, site_url: str) -> None:
        self.site_url = site_url
        # Convert to GSC format (domain property or URL)
        if site_url.startswith("http"):
            from urllib.parse import urlparse

            domain = urlparse(site_url).netloc
            self.gsc_site_url = f"sc-domain:{domain}"
        else:
            self.gsc_site_url = site_url
        print(f"🌐 Target site: {site_url}")
        print(f"🔍 GSC site: {self.gsc_site_url}")

    # ==================== GSC METHODS ====================

    def fetch_gsc_analytics(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str] = ["query"],
        row_limit: int = 1000,
    ) -> Optional[List[Dict]]:
        """Fetch search analytics from Google Search Console"""
        if not self.gsc_service:
            return self._generate_gsc_demo(start_date, end_date, dimensions)

        try:
            request = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions,
                "rowLimit": row_limit,
            }

            response = (
                self.gsc_service.searchanalytics()
                .query(siteUrl=self.gsc_site_url, body=request)
                .execute()
            )

            rows = response.get("rows", [])
            print(f"✅ GSC: Fetched {len(rows)} rows")
            return rows

        except Exception as e:
            print(f"❌ GSC: Failed to fetch - {e}")
            return self._generate_gsc_demo(start_date, end_date, dimensions)

    def _generate_gsc_demo(
        self, start_date: str, end_date: str, dimensions: List[str]
    ) -> List[Dict]:
        """Return empty list when GSC API fails - NO MOCK DATA"""
        return []

    # ==================== GA4 METHODS ====================

    def fetch_ga4_analytics(self, start_date: str, end_date: str) -> Dict:
        """Fetch analytics from Google Analytics 4"""
        if not hasattr(self, "ga4_service") or not self.ga4_service:
            return self._generate_ga4_demo(start_date, end_date)

        try:
            body = {
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "totalUsers"},
                    {"name": "screenPageViews"},
                    {"name": "averageSessionDuration"},
                    {"name": "bounceRate"},
                    {"name": "conversions"},
                ],
                "dimensions": [
                    {"name": "date"},
                    {"name": "deviceCategory"},
                    {"name": "sessionSource"},
                ],
                "limit": 10000,
            }

            response = (
                self.ga4_service.properties()
                .runReport(property=f"properties/{self.ga4_property_id}", body=body)
                .execute()
            )

            print(f"✅ GA4: Fetched analytics data")
            return response

        except Exception as e:
            print(f"❌ GA4: Failed to fetch - {e}")
            return self._generate_ga4_demo(start_date, end_date)

    def _generate_ga4_demo(self, start_date: str, end_date: str) -> Dict:
        """Return empty data when GA4 API fails - NO MOCK DATA"""
        return {"rows": []}

    def analyze_ga4_performance(self, ga4_data: Dict) -> Dict[str, Any]:
        """Analyze GA4 data"""
        if not ga4_data or not ga4_data.get("rows"):
            return {}

        try:
            # Try to get totals, or calculate from rows
            totals = ga4_data.get("totals", [])
            rows = ga4_data.get("rows", [])

            if totals and len(totals) > 0:
                total_vals = totals[0].get("metricValues", [])
                total_sessions = (
                    int(total_vals[0].get("value", 0)) if len(total_vals) > 0 else 0
                )
                total_users = (
                    int(total_vals[1].get("value", 0)) if len(total_vals) > 1 else 0
                )
                total_pageviews = (
                    int(total_vals[2].get("value", 0)) if len(total_vals) > 2 else 0
                )
                avg_duration = (
                    float(total_vals[3].get("value", 0)) if len(total_vals) > 3 else 0
                )
                bounce_rate = (
                    float(total_vals[4].get("value", 0)) if len(total_vals) > 4 else 0
                )
                conversions = (
                    int(total_vals[5].get("value", 0)) if len(total_vals) > 5 else 0
                )
            else:
                # Calculate from rows
                total_sessions = sum(
                    int(r["metricValues"][0].get("value", 0)) for r in rows
                )
                total_users = sum(
                    int(r["metricValues"][1].get("value", 0)) for r in rows
                )
                total_pageviews = sum(
                    int(r["metricValues"][2].get("value", 0)) for r in rows
                )
                avg_duration = 0
                bounce_rate = 0
                conversions = 0
                for r in rows:
                    if len(r["metricValues"]) > 4:
                        bounce_rate += float(r["metricValues"][4].get("value", 0))
                    if len(r["metricValues"]) > 5:
                        conversions += int(r["metricValues"][5].get("value", 0))
                if rows:
                    bounce_rate = bounce_rate / len(rows)

            device_breakdown = {}
            source_breakdown = {}

            # Get device/source breakdown with separate query
            try:
                body_dim = {
                    "dateRanges": [
                        {"startDate": "2026-01-01", "endDate": "2026-12-31"}
                    ],
                    "metrics": [{"name": "sessions"}],
                    "dimensions": [
                        {"name": "deviceCategory"},
                        {"name": "sessionSource"},
                    ],
                    "limit": 20,
                }
                dim_response = (
                    self.ga4_service.properties()
                    .runReport(
                        property=f"properties/{self.ga4_property_id}", body=body_dim
                    )
                    .execute()
                )

                for row in dim_response.get("rows", []):
                    device = row["dimensionValues"][0].get("value", "unknown")
                    source = row["dimensionValues"][1].get("value", "unknown")
                    sessions = int(row["metricValues"][0].get("value", 0))
                    device_breakdown[device] = (
                        device_breakdown.get(device, 0) + sessions
                    )
                    source_breakdown[source] = (
                        source_breakdown.get(source, 0) + sessions
                    )
            except:
                pass

            return {
                "total_sessions": total_sessions,
                "total_users": total_users,
                "total_pageviews": total_pageviews,
                "avg_session_duration": round(avg_duration, 1),
                "bounce_rate": round(bounce_rate, 3),
                "conversions": conversions,
                "conversion_rate": round(conversions / total_sessions, 4)
                if total_sessions > 0
                else 0,
                "device_breakdown": device_breakdown,
                "source_breakdown": source_breakdown,
            }

        except Exception as e:
            print(f"⚠️  GA4: Analysis error - {e}")
            return {}

    # ==================== META METHODS ====================

    def fetch_meta_insights(self, start_date: str, end_date: str) -> Dict:
        """Fetch insights from Meta Graph API - including posts, audience, content"""
        if not self.meta_access_token or not self.meta_page_id:
            return self._generate_meta_demo()

        try:
            # 1. Exchange user access token for Page access token
            page_token_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}"
            page_token_params = {
                "fields": "access_token",
                "access_token": self.meta_access_token,
            }
            token_response = self.session.get(
                page_token_url, params=page_token_params, timeout=10
            )
            token_data = token_response.json()

            if "error" in token_data:
                print(
                    f"❌ Meta: Failed to get page token - {token_data.get('error', {}).get('message', 'Unknown')}"
                )
                # Fall back to trying with user token (works for some older pages)
                page_access_token = self.meta_access_token
            else:
                page_access_token = token_data.get(
                    "access_token", self.meta_access_token
                )

            # 2. Page info (followers)
            info_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}"
            info_params = {
                "fields": "followers_count,fan_count",
                "access_token": page_access_token,
            }
            info_response = self.session.get(info_url, params=info_params, timeout=10)
            info_data = info_response.json()

            if "error" in info_data:
                print(
                    f"❌ Meta API Error: {info_data.get('error', {}).get('message', 'Unknown error')}"
                )
                return self._generate_meta_demo()

            # 3. Basic metrics
            metrics_data = []
            metric_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}/insights/page_impressions_unique"
            response = self.session.get(
                metric_url, params={"access_token": page_access_token}, timeout=30
            )
            data = response.json()
            if "data" in data:
                metrics_data.extend(data["data"])

            # 4. Recent posts with engagement
            posts_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}/posts"
            posts_params = {
                "access_token": page_access_token,
                "limit": "10",
                "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            }
            posts_response = self.session.get(
                posts_url, params=posts_params, timeout=30
            )
            posts_data = posts_response.json()

            # 5. Audience demographics
            audience_data = {}
            try:
                gender_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}/insights/page_fans_gender"
                gender_resp = self.session.get(
                    gender_url, params={"access_token": page_access_token}, timeout=30
                )
                gender_json = gender_resp.json()
                if "data" in gender_json:
                    audience_data["gender"] = gender_json["data"]
            except:
                pass

            try:
                age_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}/insights/page_fans_age"
                age_resp = self.session.get(
                    age_url, params={"access_token": page_access_token}, timeout=30
                )
                age_json = age_resp.json()
                if "data" in age_json:
                    audience_data["age"] = age_json["data"]
            except:
                pass

            # 6. Content performance
            content_data = {}
            try:
                content_url = f"https://graph.facebook.com/v21.0/{self.meta_page_id}/insights/page_posts_impressions"
                content_resp = self.session.get(
                    content_url, params={"access_token": page_access_token}, timeout=30
                )
                content_json = content_resp.json()
                if "data" in content_json:
                    content_data["impressions"] = content_json["data"]
            except:
                pass

            # 7. Ads insights (if user has ad account linked)
            ads_data = {}
            try:
                ads_url = (
                    f"https://graph.facebook.com/v21.0/{self.meta_page_id}/insights"
                )
                ads_params = {
                    "access_token": page_access_token,
                    "metric": "page_ads_impressions,page_ads_reach,page_daily_ad_spend",
                    "period": "day",
                }
                ads_resp = self.session.get(ads_url, params=ads_params, timeout=30)
                ads_json = ads_resp.json()
                if "data" in ads_json:
                    ads_data = ads_json["data"]
            except:
                pass

            # 8. Campaign insights (if available via adaccount)
            campaigns_data = []
            try:
                me_url = "https://graph.facebook.com/v21.0/me/accounts"
                me_resp = self.session.get(
                    me_url, params={"access_token": page_access_token}, timeout=30
                )
                accounts_json = me_resp.json()
                if "data" in accounts_json and len(accounts_json["data"]) > 0:
                    ad_account_id = accounts_json["data"][0].get("id")
                    if ad_account_id:
                        campaigns_url = f"https://graph.facebook.com/v21.0/{ad_account_id}/campaigns"
                        campaigns_params = {
                            "access_token": page_access_token,
                            "fields": "id,name,status,daily_budget,objective",
                            "limit": "10",
                        }
                        campaigns_resp = self.session.get(
                            campaigns_url, params=campaigns_params, timeout=30
                        )
                        campaigns_json = campaigns_resp.json()
                        if "data" in campaigns_json:
                            campaigns_data = campaigns_json["data"]
            except:
                pass

            result = {
                "data": metrics_data,
                "fan_count": info_data.get(
                    "followers_count", info_data.get("fan_count", 0)
                ),
                "posts": posts_data.get("data", []) if "data" in posts_data else [],
                "audience": audience_data,
                "content": content_data,
                "ads": ads_data,
                "campaigns": campaigns_data,
            }

            print(f"✅ Meta: Fetched {len(metrics_data)} metric groups")
            print(f"   Followers: {info_data.get('followers_count', 0):,}")
            print(f"   Recent Posts: {len(result.get('posts', []))}")
            return result

        except Exception as e:
            print(f"❌ Meta: Failed to fetch - {e}")
            return self._generate_meta_demo()

    def _generate_meta_demo(self) -> Dict:
        """Return empty data when Meta API fails - NO MOCK DATA"""
        return {
            "error": "Meta access token expired or invalid",
            "data": [],
            "fan_count": 0,
            "available": False,
        }

    def analyze_meta_performance(self, meta_data: Dict) -> Dict[str, Any]:
        """Analyze Meta insights data"""
        if not meta_data or not meta_data.get("data"):
            return {}

        try:
            metrics = {}
            for item in meta_data["data"]:
                name = item["name"]
                values = item.get("values", [])

                if item.get("period") == "lifetime":
                    metrics[name] = values[0].get("value", 0) if values else 0
                else:
                    total = sum(v.get("value", 0) for v in values)
                    metrics[name] = total

            impressions = metrics.get("page_impressions_unique", 0)
            engaged = int(
                impressions * 0.05
            )  # Estimate ~5% engagement from impressions
            fans = meta_data.get("fan_count", 5420)

            return {
                "total_impressions": impressions,
                "total_engaged_users": engaged,
                "total_fans": fans,
                "engagement_rate": round(engaged / impressions, 4)
                if impressions > 0
                else 0,
                "avg_daily_impressions": impressions // 7 if impressions > 0 else 0,
                "avg_daily_engaged": engaged // 7 if engaged > 0 else 0,
                "page_views": metrics.get("page_views", 0),
                "post_engagements": metrics.get("page_post_engagements", 0),
                # New: Posts data
                "recent_posts": self._analyze_posts(meta_data.get("posts", [])),
                # New: Audience demographics
                "audience": self._analyze_audience(meta_data.get("audience", {})),
                # New: Ads data
                "ads_insights": self._analyze_ads(
                    meta_data.get("ads", []), meta_data.get("campaigns", [])
                ),
            }

        except Exception as e:
            print(f"⚠️  Meta: Analysis error - {e}")
            return {}

    def _analyze_posts(self, posts: List[Dict]) -> List[Dict]:
        """Analyze recent posts for engagement metrics"""
        analyzed = []
        for post in posts[:10]:  # Top 10 recent posts
            try:
                likes = post.get("likes", {})
                likes_count = (
                    likes.get("summary", {}).get("total_count", 0)
                    if isinstance(likes, dict)
                    else 0
                )

                comments = post.get("comments", {})
                comments_count = (
                    comments.get("summary", {}).get("total_count", 0)
                    if isinstance(comments, dict)
                    else 0
                )

                shares_count = (
                    post.get("shares", {}).get("count", 0) if post.get("shares") else 0
                )

                analyzed.append(
                    {
                        "id": post.get("id", ""),
                        "message": (post.get("message", "")[:100] + "...")
                        if post.get("message")
                        else "(No message)",
                        "created_time": post.get("created_time", ""),
                        "likes": likes_count,
                        "comments": comments_count,
                        "shares": shares_count,
                        "total_engagement": likes_count + comments_count + shares_count,
                    }
                )
            except:
                pass

        # Sort by engagement
        analyzed.sort(key=lambda x: x.get("total_engagement", 0), reverse=True)
        return analyzed

    def _analyze_audience(self, audience: Dict) -> Dict:
        """Analyze audience demographics"""
        result = {"gender": {}, "age": {}}

        # Gender breakdown
        gender_data = audience.get("gender", [])
        if gender_data and len(gender_data) > 0:
            values = gender_data[0].get("values", [])
            for v in values:
                result["gender"][v.get("value", "unknown")] = v.get("end_time", 0)

        # Age breakdown
        age_data = audience.get("age", [])
        if age_data and len(age_data) > 0:
            values = age_data[0].get("values", [])
            for v in values:
                result["age"][v.get("value", "unknown")] = v.get("end_time", 0)

        return result

    def _analyze_ads(self, ads_data: List[Dict], campaigns_data: List[Dict]) -> Dict:
        """Analyze ads insights and campaigns"""
        result = {
            "metrics": {},
            "campaigns": [],
            "total_spend": 0,
            "total_impressions": 0,
            "total_reach": 0,
        }

        # Parse ads metrics
        for metric in ads_data:
            name = metric.get("name", "")
            values = metric.get("values", [])
            if values:
                total = sum(v.get("value", 0) for v in values)
                result["metrics"][name] = total
                if name == "page_daily_ad_spend":
                    result["total_spend"] = total
                elif name == "page_ads_impressions":
                    result["total_impressions"] = total
                elif name == "page_ads_reach":
                    result["total_reach"] = total

        # Parse campaigns
        for campaign in campaigns_data:
            result["campaigns"].append(
                {
                    "id": campaign.get("id"),
                    "name": campaign.get("name"),
                    "status": campaign.get("status"),
                    "budget": campaign.get("daily_budget"),
                    "objective": campaign.get("objective"),
                }
            )

        # If no ads data, try to fetch from ad account level
        if not result["metrics"] and self.meta_access_token:
            try:
                me_url = "https://graph.facebook.com/v21.0/me/adaccounts"
                resp = self.session.get(
                    me_url, params={"access_token": self.meta_access_token}, timeout=30
                )
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    ad_account_id = data["data"][0].get("id")
                    if ad_account_id:
                        insights_url = (
                            f"https://graph.facebook.com/v21.0/{ad_account_id}/insights"
                        )
                        params = {
                            "access_token": self.meta_access_token,
                            "date_preset": "last_30_days",
                            "fields": "spend,impressions,reach,clicks,cpm,cpc,ctr",
                        }
                        insights_resp = self.session.get(
                            insights_url, params=params, timeout=30
                        )
                        insights_data = insights_resp.json()
                        if "data" in insights_data and len(insights_data["data"]) > 0:
                            insight = insights_data["data"][0]
                            result["metrics"] = {
                                "spend": float(insight.get("spend", 0)),
                                "impressions": int(insight.get("impressions", 0)),
                                "reach": int(insight.get("reach", 0)),
                                "clicks": int(insight.get("clicks", 0)),
                                "cpm": float(insight.get("cpm", 0)),
                                "cpc": float(insight.get("cpc", 0)),
                                "ctr": float(insight.get("ctr", 0)),
                            }
                            result["total_spend"] = result["metrics"].get("spend", 0)
                            result["total_impressions"] = result["metrics"].get(
                                "impressions", 0
                            )
                            result["total_reach"] = result["metrics"].get("reach", 0)
            except Exception as e:
                print(f"⚠️  Meta Ads: Could not fetch ad account insights - {e}")

        return result

    # ==================== UNIFIED ANALYSIS ====================

    def calculate_overall_scores(
        self, gsc_data: Dict, ga4_data: Dict, meta_data: Dict
    ) -> Dict[str, float]:
        """Calculate weighted overall performance scores"""
        scores = {}

        if gsc_data:
            total_clicks = gsc_data.get("total_clicks", 0)
            total_impressions = gsc_data.get("total_impressions", 0)
            avg_position = gsc_data.get("average_position", 50)

            visibility = min(100, (total_clicks / 100) + (total_impressions / 1000))
            content_score = max(0, 100 - (avg_position - 1) * 5)
            scores["search_visibility"] = min(100, (visibility + content_score) / 2)
        else:
            scores["search_visibility"] = 50

        if ga4_data:
            bounce_rate = ga4_data.get("bounce_rate", 1.0)
            conversion_rate = ga4_data.get("conversion_rate", 0)

            ga4_score = 100 - (bounce_rate * 100) + (conversion_rate * 500)
            scores["ga4_performance"] = max(0, min(100, ga4_score))
        else:
            scores["ga4_performance"] = 50

        if meta_data:
            engagement_rate = meta_data.get("engagement_rate", 0)
            meta_score = engagement_rate * 1000
            scores["meta_performance"] = min(100, meta_score)
        else:
            scores["meta_performance"] = 50

        scores["technical_health"] = 75
        scores["content_performance"] = 75

        overall = sum(scores[cat] * weight for cat, weight in self.weights.items())
        scores["overall"] = round(overall, 2)

        return scores

    def generate_unified_report(
        self,
        site_url: str,
        days: int = 30,
        channels: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive multi-channel report"""
        channels = channels or ["gsc", "ga4", "meta"]

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Calculate actual days from dates
        actual_days = (
            datetime.strptime(end_date, "%Y-%m-%d")
            - datetime.strptime(start_date, "%Y-%m-%d")
        ).days + 1

        print(f"\n{'=' * 60}")
        print(f"📊 DATA ANALYST REPORT")
        print(f"{'=' * 60}")
        print(f"Website: {site_url}")
        print(f"Period: {start_date} to {end_date} ({actual_days} days)")
        print(f"Channels: {', '.join(channels)}")
        print(f"{'=' * 60}\n")

        gsc_analysis = {}
        ga4_analysis = {}
        meta_analysis = {}

        if "gsc" in channels:
            print("📈 Fetching GSC data...")
            gsc_data = self.fetch_gsc_analytics(start_date, end_date, ["query"])
            if gsc_data:
                gsc_analysis = self._analyze_gsc(gsc_data)
                self.performance_data = gsc_analysis

        if "ga4" in channels:
            print("📊 Fetching GA4 data...")
            ga4_raw = self.fetch_ga4_analytics(start_date, end_date)
            if ga4_raw:
                ga4_analysis = self.analyze_ga4_performance(ga4_raw)
                self.ga4_data = ga4_analysis

            # GA4 events fetching disabled until API method is restored
            # print("📊 Fetching GA4 events...")

        if "meta" in channels:
            print("📱 Fetching Meta insights...")
            meta_raw = self.fetch_meta_insights(start_date, end_date)
            if meta_raw:
                meta_analysis = self.analyze_meta_performance(meta_raw)
                self.meta_data = meta_analysis

        scores = self.calculate_overall_scores(
            gsc_analysis, ga4_analysis, meta_analysis
        )

        report = {
            "site_url": site_url,
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "overall_score": scores["overall"],
            "scores": scores,
            "channels": {
                "gsc": gsc_analysis,
                "ga4": ga4_analysis,
                "meta": meta_analysis,
            },
            "recommendations": self._generate_recommendations(
                gsc_analysis, ga4_analysis, meta_analysis, scores
            ),
            "summary": self._generate_summary(
                gsc_analysis, ga4_analysis, meta_analysis, scores
            ),
        }

        self._print_report(report)

        return report

    def _analyze_gsc(self, query_data: List[Dict]) -> Dict[str, Any]:
        """Analyze GSC query data"""
        if not query_data:
            return {}

        total_clicks = sum(row.get("clicks", 0) for row in query_data)
        total_impressions = sum(row.get("impressions", 0) for row in query_data)
        avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        avg_position = (
            sum(
                row.get("position", 0) * row.get("impressions", 0) for row in query_data
            )
            / total_impressions
            if total_impressions > 0
            else 0
        )

        top_3 = sum(1 for row in query_data if row.get("position", 99) <= 3)
        positions_4_10 = sum(
            1 for row in query_data if 3 < row.get("position", 99) <= 10
        )

        return {
            "total_queries": len(query_data),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "average_ctr": round(avg_ctr, 4),
            "average_position": round(avg_position, 2),
            "top_3_rankings": top_3,
            "positions_4_10": positions_4_10,
            "top_queries": query_data[:10],
        }

    def _generate_recommendations(
        self,
        gsc: Dict,
        ga4: Dict,
        meta: Dict,
        scores: Dict,
    ) -> List[Dict]:
        """Generate cross-channel recommendations"""
        recommendations = []

        if ga4:
            if ga4.get("bounce_rate", 0) > 0.5:
                recommendations.append(
                    {
                        "priority": "High",
                        "channel": "GA4",
                        "title": "Reduce Bounce Rate",
                        "description": f"Bounce rate is {ga4.get('bounce_rate', 0):.1%}. Improve content engagement.",
                        "impact": "Medium",
                        "effort": "Medium",
                    }
                )

            top_sources = sorted(
                ga4.get("source_breakdown", {}).items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]
            if top_sources:
                recommendations.append(
                    {
                        "priority": "Medium",
                        "channel": "GA4",
                        "title": "Top Traffic Sources",
                        "description": f"Main sources: {', '.join(s[0] for s in top_sources)}",
                        "impact": "Info",
                        "effort": "Low",
                    }
                )

        if meta:
            engagement = meta.get("engagement_rate", 0)
            if engagement < 0.05:
                recommendations.append(
                    {
                        "priority": "High",
                        "channel": "Meta",
                        "title": "Boost Engagement",
                        "description": f"Engagement rate {engagement:.2%} is below average. Post more engaging content.",
                        "impact": "High",
                        "effort": "Medium",
                    }
                )

        if gsc:
            pos_4_10 = gsc.get("positions_4_10", 0)
            if pos_4_10 > 5:
                recommendations.append(
                    {
                        "priority": "High",
                        "channel": "GSC",
                        "title": "Improve Page 1 Rankings",
                        "description": f"{pos_4_10} queries ranking 4-10. Optimize content for top 3.",
                        "impact": "High",
                        "effort": "Medium",
                    }
                )

        return recommendations[:8]

    def _generate_summary(
        self,
        gsc: Dict,
        ga4: Dict,
        meta: Dict,
        scores: Dict,
    ) -> str:
        """Generate executive summary"""
        score = scores.get("overall", 0)
        grade = (
            "A"
            if score >= 90
            else "B"
            if score >= 80
            else "C"
            if score >= 70
            else "D"
            if score >= 60
            else "F"
        )

        summary = f"""
## Executive Summary

**Overall Performance: {score:.1f}/100 (Grade {grade})**

### Channel Performance
"""
        if gsc:
            summary += f"- **Search (GSC)**: {gsc.get('total_clicks', 0):,} clicks, {gsc.get('average_position', 0):.1f} avg position\n"
        if ga4:
            summary += f"- **Web (GA4)**: {ga4.get('total_sessions', 0):,} sessions, {ga4.get('bounce_rate', 0):.1%} bounce rate\n"
        if meta:
            summary += f"- **Social (Meta)**: {meta.get('total_impressions', 0):,} impressions, {meta.get('total_fans', 0):,} followers\n"

        return summary

    def _print_report(self, report: Dict) -> None:
        """Print formatted report"""
        scores = report.get("scores", {})
        channels = report.get("channels", {})

        print("\n📊 PERFORMANCE SCORES")
        print("-" * 40)
        print(f"Overall Score:      {scores.get('overall', 0):.1f}/100")
        print(f"Search Visibility: {scores.get('search_visibility', 0):.1f}/100")
        print(f"GA4 Performance:   {scores.get('ga4_performance', 0):.1f}/100")
        print(f"Meta Performance:  {scores.get('meta_performance', 0):.1f}/100")

        gsc = channels.get("gsc", {})
        ga4 = channels.get("ga4", {})
        meta = channels.get("meta", {})

        if gsc:
            print(f"\n🔍 GSC PERFORMANCE")
            print("-" * 40)
            print(f"Total Clicks: {gsc.get('total_clicks', 0):,}")
            print(f"Total Impressions: {gsc.get('total_impressions', 0):,}")
            print(f"Average CTR: {gsc.get('average_ctr', 0):.2%}")
            print(f"Average Position: {gsc.get('average_position', 0):.1f}")

        if ga4:
            print(f"\n📊 GA4 PERFORMANCE")
            print("-" * 40)
            print(f"Total Sessions: {ga4.get('total_sessions', 0):,}")
            print(f"Total Users: {ga4.get('total_users', 0):,}")
            print(f"Bounce Rate: {ga4.get('bounce_rate', 0):.1%}")
            print(f"Conversions: {ga4.get('conversions', 0)}")

        if meta:
            print(f"\n📱 META PERFORMANCE")
            print("-" * 40)
            print(f"Total Impressions: {meta.get('total_impressions', 0):,}")
            print(f"Engaged Users: {meta.get('total_engaged_users', 0):,}")
            print(f"Page Fans: {meta.get('total_fans', 0):,}")
            print(f"Engagement Rate: {meta.get('engagement_rate', 0):.2%}")

        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 TOP RECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. [{rec.get('priority', 'Medium')}] {rec.get('title', '')}")
                print(f"   Channel: {rec.get('channel', 'All')}")

        print(f"\n{'=' * 60}")
        print("✅ Analysis complete!")
        print(f"{'=' * 60}\n")

    def export_report(self, report: Dict, output_path: str) -> None:
        """Export report to JSON"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"✅ Report exported to: {output_path}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

    def export_html_dashboard(
        self,
        report: Dict,
        output_path: str,
        trends: Optional[Dict] = None,
        growth_recommendations: Optional[List[Dict]] = None,
        comparison_data: Optional[Dict] = None,
        report_type: str = "standard",
        start_date: str = None,
        end_date: str = None,
        days: int = 30,
    ) -> str:
        """Generate a fully dynamic C-suite executive dashboard with calendar filters and interactive charts"""
        site_name = (
            report.get("site_url", "website")
            .replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
        )
        scores = report.get("scores", {})
        channels = report.get("channels", {})
        gsc = channels.get("gsc", {})
        ga4 = channels.get("ga4", {})
        meta = channels.get("meta", {})

        if hasattr(self, "ga4_events") and self.ga4_events:
            ga4["events"] = self.ga4_events

        days = report.get("analysis_period_days", 30)

        # Calculate comparison metrics for monthly report
        comparison_html = ""
        if comparison_data and report_type == "monthly":
            prev_report = comparison_data.get("previous", {})
            prev_channels = prev_report.get("channels", {})
            prev_gsc = prev_channels.get("gsc", {})
            prev_ga4 = prev_channels.get("ga4", {})
            prev_meta = prev_channels.get("meta", {})

            # Calculate differences
            gsc_clicks_diff = gsc.get("total_clicks", 0) - prev_gsc.get(
                "total_clicks", 0
            )
            gsc_clicks_pct = (
                (gsc_clicks_diff / prev_gsc.get("total_clicks", 1)) * 100
                if prev_gsc.get("total_clicks", 0) > 0
                else 0
            )

            ga4_sessions_diff = ga4.get("total_sessions", 0) - prev_ga4.get(
                "total_sessions", 0
            )
            ga4_sessions_pct = (
                (ga4_sessions_diff / prev_ga4.get("total_sessions", 1)) * 100
                if prev_ga4.get("total_sessions", 0) > 0
                else 0
            )

            meta_impressions_diff = meta.get("total_impressions", 0) - prev_meta.get(
                "total_impressions", 0
            )
            meta_impressions_pct = (
                (meta_impressions_diff / prev_meta.get("total_impressions", 1)) * 100
                if prev_meta.get("total_impressions", 0) > 0
                else 0
            )

            overall_diff = scores.get("overall", 0) - prev_report.get("scores", {}).get(
                "overall", 0
            )

            comparison_html = self._generate_comparison_html(
                gsc,
                prev_gsc,
                ga4,
                prev_ga4,
                meta,
                prev_meta,
                scores,
                prev_report.get("scores", {}),
                comparison_data.get("prev_start", ""),
                comparison_data.get("prev_end", ""),
            )

        if growth_recommendations:
            final_recommendations = growth_recommendations
        else:
            final_recommendations = report.get("recommendations", [])

        # Generate AI-powered insights
        ai_insights = None
        if (
            self.openrouter_api_key
            and self.openrouter_api_key
            != "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        ):
            print("🤖 Generating AI-powered insights...")
            ai_insights = self.generate_ai_insights(gsc, ga4, meta, scores)
            if ai_insights:
                print("✅ AI insights integrated into dashboard")

        # Determine trend
        trend_html = ""
        if trends and trends.get("overall"):
            t = trends["overall"]
            direction = t.get("direction", "stable")
            change = t.get("score_change", 0)
            if direction == "up":
                trend_html = (
                    '<span class="trend-up">[+' + f"{change:.1f}" + " pts]</span>"
                )
            elif direction == "down":
                trend_html = (
                    '<span class="trend-down">[' + f"{change:.1f}" + " pts]</span>"
                )
            else:
                trend_html = '<span class="trend-stable">[Stable]</span>'

        # Serialize data for JavaScript
        import json

        gsc_json = json.dumps(gsc, default=str)
        ga4_json = json.dumps(ga4, default=str)
        meta_json = json.dumps(meta, default=str)
        scores_json = json.dumps(scores, default=str)
        recommendations_json = json.dumps(final_recommendations[:10], default=str)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_name} - Executive Analytics Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #f8f9fa; color: #1a1a1a; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 40px; background: white; min-height: 100vh; }}
        
        /* Header */
        .header {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 35px 40px; margin: -40px -40px 40px -40px; }}
        .header-top {{ display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 2.2em; font-weight: 300; letter-spacing: 1px; }}
        .header .subtitle {{ font-size: 0.95em; opacity: 0.85; font-weight: 300; }}
        
        /* Filter Bar */
        .filter-bar {{ background: #fff; border: 1px solid #e0e0e0; padding: 20px 25px; margin-bottom: 35px; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }}
        .filter-bar label {{ font-weight: 600; color: #333; font-size: 0.9em; }}
        .filter-bar input {{ padding: 12px 15px; font-size: 1em; border: 2px solid #1a1a1a; border-radius: 6px; width: 220px; background: #fff; cursor: pointer; }}
        .filter-bar input:hover {{ border-color: #4a4a4a; }}
        .filter-bar button {{ padding: 12px 30px; font-size: 1em; background: #198754; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }}
        .filter-bar button:hover {{ background: #146c43; }}
        .filter-info {{ color: #666; font-size: 0.9em; }}
        
        /* Sections */
        .section {{ margin-bottom: 45px; }}
        .section-title {{ font-size: 1.1em; font-weight: 600; color: #1a1a1a; border-bottom: 2px solid #1a1a1a; padding-bottom: 12px; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1.5px; }}
        
        /* Cards */
        .card {{ border: 1px solid #e0e0e0; padding: 25px; margin-bottom: 20px; border-radius: 6px; }}
        .card h2 {{ font-size: 0.95em; font-weight: 600; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; color: #555; border-bottom: 1px solid #eee; padding-bottom: 12px; }}
        
        /* Grid */
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
        .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }}
        
        /* Executive Summary */
        .exec-summary {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: white; padding: 35px 40px; margin: -40px -40px 40px -40px; }}
        .exec-summary h2 {{ color: white; border-bottom: 1px solid rgba(255,255,255,0.2); }}
        .exec-summary .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; margin-top: 25px; }}
        .exec-summary .summary-item {{ text-align: center; }}
        .exec-summary .summary-value {{ font-size: 2.8em; font-weight: 300; }}
        .exec-summary .summary-label {{ font-size: 0.8em; opacity: 0.75; text-transform: uppercase; letter-spacing: 1px; }}
        
        /* Metrics */
        .score-display {{ text-align: center; padding: 20px; }}
        .score {{ font-size: 3em; font-weight: 300; line-height: 1; }}
        .score-label {{ font-size: 0.8em; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }}
        
        .metric {{ display: flex; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid #f0f0f0; }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        .metric-value {{ font-weight: 600; font-size: 1.05em; }}
        
        /* Color classes */
        .score-good {{ color: #198754; }}
        .score-neutral {{ color: #6c757d; }}
        .score-bad {{ color: #dc3545; }}
        .metric-good {{ color: #198754; }}
        .metric-bad {{ color: #dc3545; }}
        .trend-up {{ color: #198754; font-weight: 600; }}
        .trend-down {{ color: #dc3545; font-weight: 600; }}
        .trend-stable {{ color: #6c757d; }}
        
        /* Charts */
        .chart-container {{ position: relative; height: 280px; margin: 15px 0; }}
        
        /* Recommendations */
        .recommendation {{ border-left: 4px solid #1a1a1a; padding: 20px 25px; margin: 18px 0; background: #fafafa; border-radius: 0 6px 6px 0; }}
        .recommendation.high {{ border-left-color: #dc3545; background: #fff5f5; }}
        .recommendation.growth {{ border-left-color: #198754; background: #f0fff4; }}
        .rec-priority {{ font-size: 0.75em; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }}
        .rec-title {{ font-weight: 600; margin-bottom: 10px; font-size: 1.05em; }}
        .rec-desc {{ color: #555; font-size: 0.95em; line-height: 1.5; }}
        .rec-action {{ margin-top: 14px; padding-top: 14px; border-top: 1px solid #ddd; font-size: 0.9em; color: #333; }}
        
        /* Insights */
        .insight {{ padding: 18px 22px; margin: 12px 0; background: #f8f9fa; border-left: 3px solid #666; border-radius: 0 4px 4px 0; }}
        
        /* Footer */
        .footer {{ margin-top: 50px; padding-top: 25px; border-top: 1px solid #ddd; font-size: 0.8em; color: #888; text-align: center; }}
        
        /* Responsive */
        @media (max-width: 1200px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} .exec-summary .summary-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} .grid-2 {{ grid-template-columns: 1fr; }} .container {{ padding: 20px; }} .header {{ margin: -20px -20px 30px -20px; padding: 25px; }} .filter-bar {{ flex-direction: column; align-items: stretch; }} .filter-bar input {{ width: 100%; }} }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-top">
                <div>
                    <h1>{site_name}</h1>
                    <div class="subtitle">Executive Analytics Report</div>
                </div>
                <div style="text-align: right; opacity: 0.85;">
                    {trend_html}<br>
                    <span style="font-size: 0.85em;">Vincent John Rodriguez</span>
                </div>
            </div>
        </div>

        <!-- Date Filter -->
        <div class="filter-bar">
            <label>Date Range:</label>
            <input type="text" id="dateRange" placeholder="Select date range...">
            <button onclick="applyDateFilter()">Apply Filter</button>
            <span class="filter-info" id="filterInfo">Showing data for: Last {
            days
        } days</span>
        </div>

        <!-- Executive Summary -->
        {
            comparison_html
            if comparison_html
            else f'''
        <div class="exec-summary">
            <h2>Executive Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value" id="execScore">{scores.get("overall", 0):.1f}</div>
                    <div class="summary-label">Overall Score</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value" id="execClicks">{gsc.get("total_clicks", 0):,}</div>
                    <div class="summary-label">Search Clicks</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value" id="execSessions">{ga4.get("total_sessions", 0):,}</div>
                    <div class="summary-label">Web Sessions</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value" id="execImpressions">{meta.get("total_impressions", 0):,}</div>
                    <div class="summary-label">Social Impressions</div>
                </div>
            </div>
        </div>'''
        }

        <!-- Performance Scores -->
        <div class="section">
            <h2 class="section-title">Performance Scores</h2>
            <div class="grid">
                <div class="card">
                    <div class="score-display">
                        <div class="score" id="scoreOverall">{
            scores.get("overall", 0):.1f}</div>
                        <div class="score-label">Overall Score /100</div>
                    </div>
                </div>
                <div class="card">
                    <h2>Search Visibility</h2>
                    <div class="metric">
                        <span class="metric-label">Score</span>
                        <span class="metric-value" id="scoreGsc">{
            scores.get("search_visibility", 0):.1f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Clicks</span>
                        <span class="metric-value" id="gscClicks">{
            gsc.get("total_clicks", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Impressions</span>
                        <span class="metric-value" id="gscImpressions">{
            gsc.get("total_impressions", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg CTR</span>
                        <span class="metric-value" id="gscCtr">{
            gsc.get("average_ctr", 0):.2%}</span>
                    </div>
                </div>
                <div class="card">
                    <h2>Web Analytics</h2>
                    <div class="metric">
                        <span class="metric-label">Score</span>
                        <span class="metric-value" id="scoreGa4">{
            scores.get("ga4_performance", 0):.1f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sessions</span>
                        <span class="metric-value" id="ga4Sessions">{
            ga4.get("total_sessions", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Users</span>
                        <span class="metric-value" id="ga4Users">{
            ga4.get("total_users", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Bounce Rate</span>
                        <span class="metric-value" id="ga4Bounce">{
            ga4.get("bounce_rate", 0):.1%}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- GA4 Events Section -->
        <div class="section" id="eventsSection">
            <h2 class="section-title">Event Tracking & Conversions</h2>
            <div class="grid-2">
                <div class="card">
                    <h2>Event Summary</h2>
                    <div class="metric">
                        <span class="metric-label">Total Events</span>
                        <span class="metric-value" id="totalEvents">{
            ga4.get("events", {}).get("total_events", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Event Types</span>
                        <span class="metric-value" id="totalEventTypes">{
            ga4.get("events", {}).get("total_event_types", 0)
        }</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sessions with Events</span>
                        <span class="metric-value" id="sessionsWithEvents">{
            ga4.get("events", {}).get("sessions_with_events", 0):,}</span>
                    </div>
                </div>
                <div class="card">
                    <h2>Top Events</h2>
                    <table style="width:100%; border-collapse: collapse; font-size: 0.85em;" id="eventsTable">
                        <tr style="border-bottom: 2px solid #000;"><th style="text-align:left; padding:8px;">Event</th><th style="text-align:right; padding:8px;">Count</th><th style="text-align:right; padding:8px;">Sessions</th></tr>
                        {
            "".join(
                f'<tr style="border-bottom: 1px solid #eee;"><td style="padding:8px;">{e.get("name", "")}</td><td style="text-align:right; padding:8px;">{e.get("count", 0):,}</td><td style="text-align:right; padding:8px;">{e.get("sessions", 0):,}</td></tr>'
                for e in ga4.get("events", {}).get("top_events", [])[:8]
            )
        }
                    </table>
                </div>
            </div>
        </div>

        <!-- Social Performance -->
        <div class="section">
            <h2 class="section-title">Social Performance</h2>
            <div class="grid-2">
                <div class="card">
                    <h2>Social Score</h2>
                    <div class="metric">
                        <span class="metric-label">Score</span>
                        <span class="metric-value" id="scoreMeta">{
            scores.get("meta_performance", 0):.1f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Impressions</span>
                        <span class="metric-value" id="metaImpressions">{
            meta.get("total_impressions", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Followers</span>
                        <span class="metric-value" id="metaFollowers">{
            meta.get("total_fans", 0):,}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Engagement</span>
                        <span class="metric-value" id="metaEngagement">{
            meta.get("engagement_rate", 0):.2%}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="section">
            <h2 class="section-title">Performance Charts</h2>
            <div class="grid-2">
                <div class="card">
                    <h2>Channel Performance Comparison</h2>
                    <div class="chart-container">
                        <canvas id="channelChart"></canvas>
                    </div>
                </div>
                <div class="card">
                    <h2>Traffic Distribution</h2>
                    <div class="chart-container">
                        <canvas id="trafficChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="grid-2">
                <div class="card">
                    <h2>Key Metrics Overview</h2>
                    <div class="chart-container">
                        <canvas id="metricsChart"></canvas>
                    </div>
                </div>
                <div class="card">
                    <h2>Engagement Rates</h2>
                    <div class="chart-container">
                        <canvas id="engagementChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detailed Tables -->
        <div class="section">
            <h2 class="section-title">Detailed Analysis</h2>
            <div class="grid-2">
                <div class="card">
                    <h2>Top Performing Queries</h2>
                    <table style="width:100%; border-collapse: collapse; font-size: 0.9em;">
                        <tr style="border-bottom: 2px solid #000;"><th style="text-align:left; padding:10px;">Query</th><th style="text-align:right; padding:10px;">Clicks</th><th style="text-align:right; padding:10px;">Position</th><th style="text-align:right; padding:10px;">CTR</th></tr>
"""

        # Add top queries
        if gsc.get("top_queries"):
            for q in gsc.get("top_queries", [])[:10]:
                query = q.get("keys", [""])[0]
                clicks = q.get("clicks", 0)
                position = q.get("position", 0)
                ctr = q.get("ctr", 0)
                html += f'<tr style="border-bottom: 1px solid #eee;"><td style="padding:10px;">{query}</td><td style="text-align:right; padding:10px;">{clicks}</td><td style="text-align:right; padding:10px;">{position:.1f}</td><td style="text-align:right; padding:10px;">{ctr:.1%}</td></tr>'

        html += f"""
                    </table>
                </div>
                <div class="card">
                    <h2>Device Breakdown</h2>
                    <table style="width:100%; border-collapse: collapse; font-size: 0.9em;">
                        <tr style="border-bottom: 2px solid #000;"><th style="text-align:left; padding:10px;">Device</th><th style="text-align:right; padding:10px;">Sessions</th><th style="text-align:right; padding:10px;">%</th></tr>
"""

        if ga4.get("device_breakdown"):
            total_sessions = ga4.get("total_sessions", 1)
            for device, sessions in ga4.get("device_breakdown", {}).items():
                pct = (sessions / total_sessions * 100) if total_sessions > 0 else 0
                html += f'<tr style="border-bottom: 1px solid #eee;"><td style="padding:10px;">{device}</td><td style="text-align:right; padding:10px;">{sessions:,}</td><td style="text-align:right; padding:10px;">{pct:.1f}%</td></tr>'

        html += f"""
                    </table>
                </div>
            </div>
        </div>

        <!-- Key Insights -->
        <div class="section">
            <h2 class="section-title">Key Insights & Analysis</h2>
            {self._generate_ai_html_insights(ai_insights, gsc, ga4, meta, scores) if ai_insights else self._generate_dynamic_insights(gsc, ga4, meta, scores)}
        </div>

        <!-- Strategic Recommendations -->
        <div class="section">
            <h2 class="section-title">Strategic Recommendations</h2>
"""

        for rec in final_recommendations[:10]:
            priority_class = (
                "high"
                if rec.get("priority") in ["Critical", "High"]
                else "growth"
                if rec.get("priority") == "Growth"
                else ""
            )
            rec_title = (
                rec.get("title", "")
                .replace("📈", "")
                .replace("📉", "")
                .replace("🔴", "")
                .replace("🎯", "")
                .replace("📝", "")
                .replace("🔗", "")
                .strip()
            )
            rec_desc = (
                rec.get("description", "")
                .replace("📈", "")
                .replace("📉", "")
                .replace("🔴", "")
                .replace("🎯", "")
                .replace("📝", "")
                .replace("🔗", "")
                .strip()
            )
            rec_action = (
                rec.get("action", rec.get("description", ""))
                .replace("📈", "")
                .replace("📉", "")
                .replace("🔴", "")
                .replace("🎯", "")
                .replace("📝", "")
                .replace("🔗", "")
                .strip()
            )
            html += f"""
            <div class="recommendation {priority_class}">
                <div class="rec-priority">{rec.get("priority", "Medium").upper()} PRIORITY</div>
                <div class="rec-title">{rec_title}</div>
                <div class="rec-desc">{rec_desc}</div>
                <div class="rec-action"><strong>Recommended Action:</strong> {rec_action}</div>
            </div>
"""

        html += f'''
        </div>

        <!-- Action Plan -->
        <div class="section">
            <h2 class="section-title">Action Plan</h2>
            {self._generate_dynamic_action_plan(gsc, ga4, meta, scores)}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>Report Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Author:</strong> Vincent John Rodriguez | <strong>Confidential</strong></p>
            <p>This report contains confidential business information. Distribution is limited to authorized personnel only.</p>
        </div>
    </div>

    <!-- Embedded Data -->
    <script>
        // Report Data
        const reportData = {{
            gsc: {gsc_json},
            ga4: {ga4_json},
            meta: {meta_json},
            scores: {scores_json},
            recommendations: {recommendations_json}
        }};

        // Initialize Date Picker - Click to open calendar
        let datePicker;
        document.addEventListener('DOMContentLoaded', function() {{
            datePicker = flatpickr("#dateRange", {{
                mode: "range",
                dateFormat: "Y-m-d",
                defaultDate: ["{start_date or (datetime.now() - timedelta(days=days or 30)).strftime("%Y-%m-%d")}", "{end_date or datetime.now().strftime("%Y-%m-%d")}"],
                maxDate: "today",
                inline: false,
                showMonths: 1,
                appendTo: document.querySelector('.filter-bar'),
                position: "below",
                onClose: function(selectedDates, dateStr, instance) {{
                    if (selectedDates.length === 2) {{
                        applyDateFilter();
                    }}
                }}
            }});
        }});

        // Chart Color Palette (Professional)
        const colors = {{
            primary: '#1a1a1a',
            secondary: '#4a4a4a',
            tertiary: '#7a7a7a',
            success: '#198754',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#0dcaf0',
            chartColors: ['#1a1a1a', '#4a4a4a', '#7a7a7a', '#198754', '#dc3545', '#0d6efd', '#ffc107']
        }};

        // Initialize Charts with proper colors
        function initCharts() {{
            const chartColors = ['#1a1a1a', '#4a4a4a', '#7a7a7a'];
            
            // Channel Performance Chart
            const channelCtx = document.getElementById('channelChart');
            if (channelCtx) {{
                new Chart(channelCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Search', 'Web', 'Social'],
                        datasets: [{{
                            label: 'Score',
                            data: [
                                reportData.scores?.search_visibility || 0, 
                                reportData.scores?.ga4_performance || 0, 
                                reportData.scores?.meta_performance || 0
                            ],
                            backgroundColor: ['#198754', '#0d6efd', '#ffc107'],
                            borderColor: ['#198754', '#0d6efd', '#ffc107'],
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
                    }}
                }});
            }}

            // Traffic Distribution Chart (Doughnut)
            const trafficCtx = document.getElementById('trafficChart');
            if (trafficCtx) {{
                new Chart(trafficCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Search Clicks', 'Web Sessions', 'Social Impressions'],
                        datasets: [{{
                            data: [
                                reportData.gsc?.total_clicks || 1, 
                                reportData.ga4?.total_sessions || 1, 
                                Math.floor((reportData.meta?.total_impressions || 1)/1000)
                            ],
                            backgroundColor: ['#198754', '#0d6efd', '#ffc107'],
                            borderColor: '#ffffff',
                            borderWidth: 3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
                    }}
                }});
            }}

            // Metrics Overview Chart (Horizontal Bar)
            const metricsCtx = document.getElementById('metricsChart');
            if (metricsCtx) {{
                new Chart(metricsCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Clicks', 'Sessions', 'Impressions (K)'],
                        datasets: [{{
                            label: 'Volume',
                            data: [
                                reportData.gsc?.total_clicks || 0, 
                                reportData.ga4?.total_sessions || 0, 
                                Math.floor((reportData.meta?.total_impressions || 0)/1000)
                            ],
                            backgroundColor: ['#198754', '#0d6efd', '#ffc107']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}

            // Engagement Chart
            const engagementCtx = document.getElementById('engagementChart');
            if (engagementCtx) {{
                new Chart(engagementCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['CTR', 'Engagement', 'Conversion'],
                        datasets: [{{
                            label: 'Rate (%)',
                            data: [
                                (reportData.gsc?.average_ctr || 0) * 100, 
                                (reportData.meta?.engagement_rate || 0) * 100, 
                                (reportData.ga4?.conversion_rate || 0) * 100
                            ],
                            backgroundColor: ['#198754', '#1a1a1a', '#dc3545']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ beginAtZero: true }} }}
                    }}
                }});
            }}

            // Traffic Distribution Chart - doughnut with colors
            new Chart(document.getElementById('trafficChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Search Clicks', 'Web Sessions', 'Social Impressions'],
                    datasets: [{{
                        data: [reportData.gsc.total_clicks || 1, reportData.ga4.total_sessions || 1, Math.floor((reportData.meta.total_impressions || 1)/1000)],
                        backgroundColor: ['#1a1a1a', '#4a4a4a', '#7a7a7a'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom' }} }}
                }}
            }});

            // Metrics Overview Chart - horizontal bar
            new Chart(document.getElementById('metricsChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Clicks', 'Sessions', 'Impressions (K)'],
                    datasets: [{{
                        label: 'Volume',
                        data: [reportData.gsc.total_clicks || 0, reportData.ga4.total_sessions || 0, Math.floor((reportData.meta.total_impressions || 0)/1000)],
                        backgroundColor: ['#198754', '#0d6efd', '#ffc107'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});

            // Engagement Chart
            new Chart(document.getElementById('engagementChart'), {{
                type: 'bar',
                data: {{
                    labels: ['CTR', 'Engagement', 'Conversion'],
                    datasets: [{{
                        label: 'Rate (%)',
                        data: [
                            (reportData.gsc.average_ctr || 0) * 100, 
                            (reportData.meta.engagement_rate || 0) * 100, 
                            (reportData.ga4.conversion_rate || 0) * 100
                        ],
                        backgroundColor: ['#198754', '#1a1a1a', '#dc3545'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});
        }}

        // Store original data for filtering
        const originalData = JSON.parse(JSON.stringify(reportData));
        let currentCharts = {{}};

        // Update metric display
        function updateMetric(id, value, isPct = false) {{
            const el = document.getElementById(id);
            if (el) {{
                el.textContent = isPct ? value.toFixed(2) + '%' : (typeof value === 'number' ? value.toLocaleString() : value);
            }}
        }}

        // Update all metrics from data
        function updateMetricsFromData(data) {{
            if (!data) return;
            
            // Executive Summary
            updateMetric('execScore', data.scores?.overall || 0);
            updateMetric('execClicks', data.gsc?.total_clicks || 0);
            updateMetric('execSessions', data.ga4?.total_sessions || 0);
            updateMetric('execImpressions', data.meta?.total_impressions || 0);
            
            // GSC Metrics
            updateMetric('scoreGsc', data.scores?.search_visibility || 0);
            updateMetric('gscClicks', data.gsc?.total_clicks || 0);
            updateMetric('gscImpressions', data.gsc?.total_impressions || 0);
            updateMetric('gscCtr', (data.gsc?.average_ctr || 0) * 100, true);
            
            // GA4 Metrics
            updateMetric('scoreGa4', data.scores?.ga4_performance || 0);
            updateMetric('ga4Sessions', data.ga4?.total_sessions || 0);
            updateMetric('ga4Users', data.ga4?.total_users || 0);
            updateMetric('ga4Bounce', (data.ga4?.bounce_rate || 0) * 100, true);
            
            // Events
            if (data.ga4?.events) {{
                updateMetric('totalEvents', data.ga4.events.total_events || 0);
                updateMetric('totalEventTypes', data.ga4.events.total_event_types || 0);
                updateMetric('sessionsWithEvents', data.ga4.events.sessions_with_events || 0);
            }}
            
            // Meta Metrics
            updateMetric('scoreMeta', data.scores?.meta_performance || 0);
            updateMetric('metaImpressions', data.meta?.total_impressions || 0);
            updateMetric('metaFollowers', data.meta?.total_fans || 0);
            updateMetric('metaEngagement', (data.meta?.engagement_rate || 0) * 100, true);
        }}

        // Re-render charts with new data
        function updateCharts(data) {{
            if (!data) return;
            
            // Destroy existing charts
            Object.values(currentCharts).forEach(chart => chart?.destroy());
            
            // Channel Performance Chart - with distinct colors
            currentCharts.channelChart = new Chart(document.getElementById('channelChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Search', 'Web', 'Social'],
                    datasets: [{{
                        label: 'Score',
                        data: [data.scores?.search_visibility || 0, data.scores?.ga4_performance || 0, data.scores?.meta_performance || 0],
                        backgroundColor: ['#1a1a1a', '#4a4a4a', '#7a7a7a'],
                        borderColor: ['#1a1a1a', '#4a4a4a', '#7a7a7a'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true, max: 100 }} }}
                }}
            }});

            // Traffic Distribution Chart - doughnut with colors
            currentCharts.trafficChart = new Chart(document.getElementById('trafficChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Search Clicks', 'Web Sessions', 'Social Impressions'],
                    datasets: [{{
                        data: [data.gsc?.total_clicks || 1, data.ga4?.total_sessions || 1, Math.floor((data.meta?.total_impressions || 1)/1000)],
                        backgroundColor: ['#1a1a1a', '#4a4a4a', '#7a7a7a'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom' }} }}
                }}
            }});

            // Metrics Overview Chart - horizontal bar
            currentCharts.metricsChart = new Chart(document.getElementById('metricsChart'), {{
                type: 'bar',
                data: {{
                    labels: ['Clicks', 'Sessions', 'Impressions (K)'],
                    datasets: [{{
                        label: 'Volume',
                        data: [data.gsc?.total_clicks || 0, data.ga4?.total_sessions || 0, Math.floor((data.meta?.total_impressions || 0)/1000)],
                        backgroundColor: ['#198754', '#0d6efd', '#ffc107'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});

            // Engagement Chart
            currentCharts.engagementChart = new Chart(document.getElementById('engagementChart'), {{
                type: 'bar',
                data: {{
                    labels: ['CTR', 'Engagement', 'Conversion'],
                    datasets: [{{
                        label: 'Rate (%)',
                        data: [
                            (data.gsc?.average_ctr || 0) * 100, 
                            (data.meta?.engagement_rate || 0) * 100, 
                            (data.ga4?.conversion_rate || 0) * 100
                        ],
                        backgroundColor: [colors.success, colors.primary, colors.danger]
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});
        }}

        // Apply Filter Function
        function applyDateFilter() {{
            const dateRange = document.getElementById('dateRange').value;
            if (dateRange) {{
                const dates = dateRange.split(' to ');
                if (dates.length === 2) {{
                    const startDate = new Date(dates[0]);
                    const endDate = new Date(dates[1]);
                    const defaultStart = new Date("{start_date or (datetime.now() - timedelta(days=days or 30)).strftime("%Y-%m-%d")}");
                    const defaultEnd = new Date("{end_date or datetime.now().strftime("%Y-%m-%d")}");
                    
                    // Calculate the day difference
                    const selectedDays = Math.round((endDate - startDate) / (1000 * 60 * 60 * 24));
                    const originalDays = {days or 30};
                    
                    // Calculate proportional ratio (capped at reasonable bounds)
                    let ratio = selectedDays / originalDays;
                    if (ratio < 0.1) ratio = 0.1;
                    if (ratio > 3) ratio = 3;
                    
                    // Update the filter info
                    document.getElementById('filterInfo').textContent = 'Showing data for: ' + dates[0] + ' to ' + dates[1] + ' (' + selectedDays + ' days - estimated)';
                    
                    // Create scaled data based on selected date range
                    const scaledData = {{
                        gsc: {{
                            total_clicks: Math.round(originalData.gsc.total_clicks * ratio),
                            total_impressions: Math.round(originalData.gsc.total_impressions * ratio),
                            average_ctr: originalData.gsc.average_ctr,
                            average_position: originalData.gsc.average_position,
                            top_queries: originalData.gsc.top_queries || []
                        }},
                        ga4: {{
                            total_sessions: Math.round(originalData.ga4.total_sessions * ratio),
                            total_users: Math.round(originalData.ga4.total_users * ratio),
                            total_pageviews: Math.round((originalData.ga4.total_pageviews || originalData.ga4.total_sessions * 2) * ratio),
                            bounce_rate: originalData.ga4.bounce_rate,
                            conversions: Math.round(originalData.ga4.conversions * ratio),
                            conversion_rate: originalData.ga4.conversion_rate,
                            device_breakdown: originalData.ga4.device_breakdown || {{}},
                            events: originalData.ga4.events || {{}}
                        }},
                        meta: {{
                            total_impressions: Math.round(originalData.meta.total_impressions * ratio),
                            total_engaged_users: Math.round(originalData.meta.total_engaged_users * ratio),
                            total_fans: originalData.meta.total_fans,
                            engagement_rate: originalData.meta.engagement_rate
                        }},
                        scores: originalData.scores
                    }};
                    
                    // Update metrics on the page
                    updateMetricsFromData(scaledData);
                    
                    // Re-render charts with scaled data
                    updateCharts(scaledData);
                    
                    // Show info banner
                    const infoBanner = document.createElement('div');
                    infoBanner.id = 'dateFilterBanner';
                    infoBanner.style.cssText = 'background: #fff3cd; border: 1px solid #ffc107; padding: 12px 20px; margin-bottom: 20px; border-radius: 6px; color: #856404;';
                    infoBanner.innerHTML = '<strong>Note:</strong> Showing estimated data based on proportional calculation (' + selectedDays + ' days vs original ' + originalDays + ' days). For accurate data, run the agent with: <code style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px; font-size: 0.9em;">python data_analyst.py {site_name} --days ' + selectedDays + '</code>';
                    
                    // Remove old banner if exists
                    const existing = document.getElementById('dateFilterBanner');
                    if (existing) existing.remove();
                    
                    // Add new banner after the filter bar
                    document.querySelector('.filter-bar').after(infoBanner);
                    
                    // Scroll to top
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }}
            }}
        }}

        // Initialize on load
        window.onload = function() {{
            initCharts();
            updateCharts(reportData);
        }};
    </script>
</body>
</html>'''

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ Dynamic executive dashboard saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Failed to save dashboard: {e}")
            return None

    def _generate_chart_data(self, gsc: Dict, ga4: Dict, meta: Dict) -> Dict:
        """Generate chart data for the dashboard"""
        return {"gsc": gsc, "ga4": ga4, "meta": meta}

    def export_streamlit_dashboard(
        self,
        report: Dict,
        output_path: str,
        trends: Optional[Dict] = None,
        growth_recommendations: Optional[List[Dict]] = None,
    ) -> str:
        """Generate a comprehensive Streamlit dashboard with metrics, charts, trends and recommendations"""
        site_name = (
            report.get("site_url", "website")
            .replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
        )
        scores = report.get("scores", {})
        channels = report.get("channels", {})
        gsc = channels.get("gsc", {})
        ga4 = channels.get("ga4", {})
        meta = channels.get("meta", {})
        recommendations = report.get("recommendations", [])

        # Use growth recommendations if provided, otherwise generate basic ones
        if growth_recommendations:
            final_recommendations = growth_recommendations
        else:
            final_recommendations = recommendations

        # Generate recommendations based on data
        gsc_recs = self._get_gsc_recommendations(gsc)
        ga4_recs = self._get_ga4_recommendations(ga4)
        meta_recs = self._get_meta_recommendations(meta)

        # Check for trend direction
        trend_indicator = ""
        if trends and trends.get("overall"):
            t = trends["overall"]
            direction = t.get("direction", "stable")
            change = t.get("score_change", 0)
            if direction == "up":
                trend_indicator = f"📈 +{change:.1f} pts"
            elif direction == "down":
                trend_indicator = f"📉 {change:.1f} pts"
            else:
                trend_indicator = "➡️ Stable"

        st_app = (
            '''"""
Streamlit Dashboard - '''
            + site_name
            + """
Auto-generated by Data Analyst Agent

Run with: streamlit run """
            + output_path
            + '''
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="'''
            + site_name
            + ''' Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .recommendation-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .insight-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .good-metric { color: #28a745; }
    .warning-metric { color: #ffc107; }
    .bad-metric { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 '''
            + site_name
            + """ Analytics Dashboard")
st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Period:** Last 30 days")
st.markdown("---")

# ==================== TREND SECTION ====================
# Note: trend_indicator is set earlier in the Python code

# ==================== OVERVIEW SECTION ====================
st.header("🎯 Performance Overview")

col1, col2, col3, col4 = st.columns(4)

overall_score = """
            + f"{scores.get('overall', 0):.1f}"
            + '''
with col1:
    st.metric("Overall Score", overall_score + "/100", 
               delta="Excellent" if float(overall_score) >= 80 else "Good" if float(overall_score) >= 60 else "Needs Work")

with col2:
    st.metric("Search Visibility", "'''
            + f"{scores.get('search_visibility', 0):.1f}"
            + '''/100')

with col3:
    st.metric("GA4 Performance", "'''
            + f"{scores.get('ga4_performance', 0):.1f}"
            + '''/100")

with col4:
    st.metric("Meta Performance", "'''
            + f"{scores.get('meta_performance', 0):.1f}"
            + '''/100")

# Score explanation
with st.expander("📖 Understanding the Scores"):
    st.markdown("""
    - **Overall Score**: Weighted average of all channels (GSC 20%, GA4 30%, Meta 20%, Technical 15%, Content 15%)
    - **Search Visibility**: Based on clicks, impressions, and ranking positions
    - **GA4 Performance**: Based on sessions, bounce rate, and conversions
    - **Meta Performance**: Based on impressions and engagement rate
    """)

st.markdown("---")

# ==================== GSC SECTION ====================
st.header("🔍 Google Search Console (SEO)")

# GSC Metrics
col_g1, col_g2, col_g3, col_g4 = st.columns(4)
with col_g1:
    st.metric("Total Clicks", "'''
            + f"{gsc.get('total_clicks', 0):,}"
            + '''")
with col_g2:
    st.metric("Total Impressions", "'''
            + f"{gsc.get('total_impressions', 0):,}"
            + '''")
with col_g3:
    ctr = gsc.get('average_ctr', 0)
    ctr_display = f"{ctr:.2%}"
    st.metric("Average CTR", ctr_display, 
               delta="Good" if ctr > 0.05 else "Needs Improvement")
with col_g4:
    pos = gsc.get('average_position', 0)
    st.metric("Avg Position", f"{pos:.1f}", 
               delta="Good" if pos <= 3 else None,
               delta_color="inverse")

# GSC Insights
st.markdown("### 💡 Insights")
if gsc.get('total_clicks', 0) < 100:
    st.markdown(f"""
    <div class="insight-box">
    <b>⚠️ Low Search Traffic:</b> Only {gsc.get('total_clicks', 0)} clicks in the last 30 days. 
    This indicates your SEO strategy needs significant improvement. Focus on ranking for relevant keywords.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="insight-box">
    <b>✅ Good Search Traffic:</b> {gsc.get('total_clicks', 0)} clicks shows decent search visibility.
    </div>
    """, unsafe_allow_html=True)

# GSC Top Queries
if gsc.get("top_queries"):
    st.markdown("### 📋 Top Performing Queries")
    queries_data = []
    for q in gsc.get("top_queries", [])[:10]:
        queries_data.append({
            "Query": q.get("keys", [""])[0],
            "Clicks": q.get("clicks", 0),
            "Impressions": q.get("impressions", 0),
            "CTR": f"{q.get('ctr', 0):.1%}",
            "Position": q.get("position", 0)
        })
    st.dataframe(pd.DataFrame(queries_data), use_container_width=True)

# GSC Recommendations
st.markdown("### 🎯 Recommendations for SEO")
for rec in gsc_recs:
    priority_color = "#dc3545" if rec['priority'] == 'High' else "#ffc107" if rec['priority'] == 'Medium' else "#28a745"
    st.markdown(f"""
    <div class="recommendation-box">
        <b style="color:{priority_color}">[{rec['priority'].upper()}]</b> <b>{rec['title']}</b><br>
        {rec['description']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== GA4 SECTION ====================
st.header("📊 Google Analytics 4 (Web Analytics)")

# GA4 Metrics
col_ga1, col_ga2, col_ga3, col_ga4 = st.columns(4)
with col_ga1:
    st.metric("Sessions", "'''
            + f"{ga4.get('total_sessions', 0):,}"
            + '''")
with col_ga2:
    st.metric("Users", "'''
            + f"{ga4.get('total_users', 0):,}"
            + '''")
with col_ga3:
    br = ga4.get('bounce_rate', 0)
    st.metric("Bounce Rate", f"{br:.1%}", 
               delta="Good" if br < 0.4 else "Needs Improvement",
               delta_color="inverse")
with col_ga4:
    st.metric("Conversions", "'''
            + f"{ga4.get('conversions', 0)}"
            + '''")

# GA4 Insights
st.markdown("### 💡 Insights")
if ga4.get('bounce_rate', 0) > 0.5:
    st.markdown(f"""
    <div class="insight-box">
    <b>⚠️ High Bounce Rate:</b> {ga4.get('bounce_rate', 0):.1%} of visitors leave without engaging.
    This suggests issues with page content, load time, or user experience.
    </div>
    """, unsafe_allow_html=True)

if ga4.get('conversions', 0) == 0:
    st.markdown(f"""
    <div class="insight-box">
    <b>⚠️ No Conversions:</b> Zero conversions in the last 30 days. 
    Review your CTAs and conversion funnel.
    </div>
    """, unsafe_allow_html=True)

# GA4 Device Breakdown
if ga4.get("device_breakdown"):
    st.markdown("### 📱 Device Breakdown")
    device_data = pd.DataFrame(list(ga4.get("device_breakdown", {}).items()), 
                               columns=['Device', 'Sessions'])
    fig = px.pie(device_data, values='Sessions', names='Device', 
                  title='Sessions by Device Type',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

# GA4 Source Breakdown
if ga4.get("source_breakdown"):
    st.markdown("### 🌐 Traffic Sources")
    source_data = ga4.get("source_breakdown", {})
    sorted_sources = dict(sorted(source_data.items(), key=lambda x: x[1], reverse=True)[:5])
    source_df = pd.DataFrame(list(sorted_sources.items()), columns=['Source', 'Sessions'])
    fig2 = px.bar(source_df, x='Source', y='Sessions', 
                   title='Top 5 Traffic Sources',
                   color='Sessions', color_continuous_scale='Blues')
    st.plotly_chart(fig2, use_container_width=True)

# GA4 Recommendations
st.markdown("### 🎯 Recommendations for GA4")
for rec in ga4_recs:
    priority_color = "#dc3545" if rec['priority'] == 'High' else "#ffc107" if rec['priority'] == 'Medium' else "#28a745"
    st.markdown(f"""
    <div class="recommendation-box">
        <b style="color:{priority_color}">[{rec['priority'].upper()}]</b> <b>{rec['title']}</b><br>
        {rec['description']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== META SECTION ====================
st.header("📱 Meta/Facebook Insights")

# Meta Metrics
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Impressions", "'''
            + f"{meta.get('total_impressions', 0):,}"
            + '''")
with col_m2:
    st.metric("Page Fans", "'''
            + f"{meta.get('total_fans', 0):,}"
            + '''")
with col_m3:
    er = meta.get('engagement_rate', 0)
    st.metric("Engagement Rate", f"{er:.2%}",
               delta="Good" if er > 0.03 else "Needs Improvement")
with col_m4:
    st.metric("Avg Daily Impressions", "'''
            + f"{meta.get('avg_daily_impressions', 0):,}"
            + '''")

# Meta Insights
st.markdown("### 💡 Insights")
if meta.get('engagement_rate', 0) > 0.03:
    st.markdown(f"""
    <div class="insight-box">
    <b>✅ Good Engagement:</b> {meta.get('engagement_rate', 0):.2%} engagement rate is above average.
    Your audience is actively interacting with your content.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="insight-box">
    <b>⚠️ Low Engagement:</b> {meta.get('engagement_rate', 0):.2%} engagement rate is below average.
    Consider posting more engaging content types (videos, polls, questions).
    </div>
    """, unsafe_allow_html=True)

# Meta Recommendations
st.markdown("### 🎯 Recommendations for Meta")
for rec in meta_recs:
    priority_color = "#dc3545" if rec['priority'] == 'High' else "#ffc107" if rec['priority'] == 'Medium' else "#28a745"
    st.markdown(f"""
    <div class="recommendation-box">
        <b style="color:{priority_color}">[{rec['priority'].upper()}]</b> <b>{rec['title']}</b><br>
        {rec['description']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== SUMMARY ====================
st.header("📈 Action Summary")

st.markdown("""
### Quick Wins (Implement This Week)
1. **Fix High Bounce Rate** - Improve page load speed and content quality
2. **Optimize for Top 3 Positions** - Target keywords where you rank 4-10
3. **Increase Posting Frequency** - Post 3-5 times per week on Meta

### Medium-Term Goals (Next 30 Days)
1. **Add Conversion Tracking** - Set up goals in GA4
2. **Create Video Content** - Higher engagement on Meta
3. **Build Backlinks** - Improve domain authority for SEO

### Long-Term Strategy
1. **Content Marketing** - Create pillar pages for main keywords
2. **Email List Growth** - Capture visitors for nurturing
3. **Paid Promotion** - Consider Facebook Ads for reach
""")

# Footer
st.markdown("---")
st.markdown("*Dashboard generated by Data Analyst Agent | For internal use only*")
'''
        )

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(st_app)
            print(f"✅ Streamlit dashboard saved to: {output_path}")
            print(f"   Run with: streamlit run {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Failed to save dashboard: {e}")
            return None

    def _generate_dynamic_insights(
        self, gsc: Dict, ga4: Dict, meta: Dict, scores: Dict
    ) -> str:
        """Generate dynamic insights based on actual data"""
        insights = []

        # GSC Insights
        gsc_clicks = gsc.get("total_clicks", 0)
        gsc_pos = gsc.get("average_position", 0)
        gsc_ctr = gsc.get("average_ctr", 0)

        if gsc_clicks < 50:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Critical: Low Search Traffic</strong><br>
                Only {gsc_clicks} clicks in the reporting period. Your SEO strategy needs immediate attention.
                Recommendation: Focus on ranking for long-tail keywords and optimize existing content.
            </div>""")
        elif gsc_clicks < 200:
            insights.append(f"""<div class="insight" style="border-left-color: #ffc107;">
                <strong>Search Traffic Below Average</strong><br>
                {gsc_clicks} clicks with {gsc_pos:.1f} average position. Room for improvement in rankings.
                Recommendation: Target keywords ranking positions 4-10 to move them to top 3.
            </div>""")
        else:
            insights.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Good Search Visibility</strong><br>
                {gsc_clicks} clicks with {gsc_pos:.1f} average position. Keep building on this momentum.
            </div>""")

        if gsc_ctr < 0.03:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Low CTR ({gsc_ctr:.1%})</strong><br>
                Click-through rate is below industry average. Optimize title tags and meta descriptions.
            </div>""")

        # GA4 Insights
        ga4_sessions = ga4.get("total_sessions", 0)
        ga4_bounce = ga4.get("bounce_rate", 0)
        ga4_conversions = ga4.get("conversions", 0)

        if ga4_bounce > 0.7:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Critical: High Bounce Rate ({ga4_bounce:.1%})</strong><br>
                Majority of visitors leave without engaging. This severely impacts conversions.
                Action: Audit landing pages, improve page load speed, enhance content quality.
            </div>""")
        elif ga4_bounce > 0.5:
            insights.append(f"""<div class="insight" style="border-left-color: #ffc107;">
                <strong>Elevated Bounce Rate ({ga4_bounce:.1%})</strong><br>
                Consider improving user engagement and content relevance.
            </div>""")
        else:
            insights.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Healthy Bounce Rate ({ga4_bounce:.1%})</strong><br>
                Good user engagement levels. Continue monitoring.
            </div>""")

        if ga4_conversions == 0:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>No Conversions Tracked</strong><br>
                Zero conversions from {ga4_sessions} sessions. This is a critical gap.
                Action: Set up conversion events in GA4 for key actions (form submissions, purchases, signups).
            </div>""")
        else:
            conv_rate = ga4.get("conversion_rate", 0) * 100
            insights.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>{ga4_conversions} Conversions Recorded</strong><br>
                {conv_rate:.2f}% conversion rate. Monitor to identify high-performing pages.
            </div>""")

        # Events data
        events = ga4.get("events", {})
        if events:
            top_events = events.get("top_events", [])
            if top_events:
                event_names = [e.get("name", "") for e in top_events[:5]]
                insights.append(f"""<div class="insight" style="border-left-color: #0dcaf0;">
                    <strong>Top Tracked Events:</strong><br>
                    {", ".join(event_names)}. These represent user interactions on your site.
                </div>""")

        # Meta Insights
        meta_impressions = meta.get("total_impressions", 0)
        meta_er = meta.get("engagement_rate", 0)
        meta_fans = meta.get("total_fans", 0)

        if meta_impressions > 100000:
            insights.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Strong Social Reach</strong><br>
                {meta_impressions:,} impressions reaching {meta_fans:,} followers.
                Leverage this reach for website traffic.
            </div>""")
        elif meta_impressions > 10000:
            insights.append(f"""<div class="insight" style="border-left-color: #ffc107;">
                <strong>Moderate Social Presence</strong><br>
                {meta_impressions:,} impressions. Increase posting frequency for better reach.
            </div>""")

        if meta_er < 0.02:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Low Engagement Rate ({meta_er:.2%})</strong><br>
                Content may not be resonating. Try video content, polls, and questions.
            </div>""")

        # Overall Score Insight
        overall = scores.get("overall", 0)
        if overall >= 70:
            insights.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Overall Performance: {overall:.1f}/100</strong><br>
                Strong multi-channel performance. Maintain current strategies.
            </div>""")
        elif overall >= 50:
            insights.append(f"""<div class="insight" style="border-left-color: #ffc107;">
                <strong>Overall Performance: {overall:.1f}/100</strong><br>
                Moderate performance across channels. Focus on improving weak areas.
            </div>""")
        else:
            insights.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Overall Performance: {overall:.1f}/100 - Needs Attention</strong><br>
                Multiple areas require improvement. Prioritize high-impact changes.
            </div>""")

        return "\n".join(insights)

    def _generate_dynamic_action_plan(
        self, gsc: Dict, ga4: Dict, meta: Dict, scores: Dict
    ) -> str:
        """Generate dynamic action plan based on actual data"""
        immediate = []
        short_term = []
        long_term = []

        gsc_clicks = gsc.get("total_clicks", 0)
        gsc_pos = gsc.get("average_position", 0)
        ga4_bounce = ga4.get("bounce_rate", 0)
        ga4_conversions = ga4.get("conversions", 0)
        meta_er = meta.get("engagement_rate", 0)

        # Immediate actions (This Week)
        if ga4_bounce > 0.5:
            immediate.append("Conduct landing page audit to reduce bounce rate")
        if ga4_conversions == 0:
            immediate.append("Set up conversion tracking in GA4")
        if gsc_clicks < 50:
            immediate.append("Fix critical SEO issues on top pages")
        if meta_er < 0.02:
            immediate.append("Review social media content strategy")

        if not immediate:
            immediate = [
                "Monitor current performance metrics",
                "Document best practices",
                "Review analytics configuration",
            ]

        # Short-Term actions (30 Days)
        if gsc_pos > 5:
            short_term.append(
                f"Optimize content for keywords ranking at position {gsc_pos:.1f}"
            )
            short_term.append("Build 3-5 quality backlinks")
        if ga4_bounce > 0.4:
            short_term.append("Improve page load speed and mobile experience")
            short_term.append("Add engaging content to reduce bounce rate")
        short_term.append("Content optimization for top-performing keywords")
        short_term.append("Increase social posting frequency to 5x/week")

        # Long-Term actions (Quarter)
        long_term.append("Develop comprehensive content marketing strategy")
        long_term.append("Set up email marketing funnel")
        long_term.append("Test paid advertising campaigns")
        long_term.append("Build strategic brand partnerships")

        html = f"""<div class="grid-3">
            <div class="card">
                <h2>Immediate (This Week)</h2>
                <ul style="margin: 15px 0 0 20px;">
                    {"".join(f'<li style="margin: 12px 0;">{item}</li>' for item in immediate)}
                </ul>
            </div>
            <div class="card">
                <h2>Short-Term (30 Days)</h2>
                <ul style="margin: 15px 0 0 20px;">
                    {"".join(f'<li style="margin: 12px 0;">{item}</li>' for item in short_term)}
                </ul>
            </div>
            <div class="card">
                <h2>Long-Term (Quarter)</h2>
                <ul style="margin: 15px 0 0 20px;">
                    {"".join(f'<li style="margin: 12px 0;">{item}</li>' for item in long_term)}
                </ul>
            </div>
        </div>"""

        return html

    def generate_ai_insights(
        self, gsc: Dict, ga4: Dict, meta: Dict, scores: Dict
    ) -> Dict[str, str]:
        """Generate comprehensive AI-powered insights using OpenRouter"""
        if (
            not self.openrouter_api_key
            or self.openrouter_api_key
            == "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        ):
            return None

        try:
            # Prepare data summary for AI
            data_summary = f"""
Website Analytics Summary:
- Search (GSC): {gsc.get("total_clicks", 0)} clicks, {gsc.get("total_impressions", 0)} impressions, {gsc.get("average_position", 0):.1f} avg position, {gsc.get("average_ctr", 0):.1%} CTR
- Web (GA4): {ga4.get("total_sessions", 0)} sessions, {ga4.get("total_users", 0)} users, {ga4.get("bounce_rate", 0):.1%} bounce rate, {ga4.get("conversions", 0)} conversions
- Social (Meta): {meta.get("total_impressions", 0):,} impressions, {meta.get("total_fans", 0):,} followers, {meta.get("engagement_rate", 0):.2%} engagement
- Overall Score: {scores.get("overall", 0):.1f}/100
- Top Events: {[e.get("name") for e in ga4.get("events", {}).get("top_events", [])[:5]]}
            """

            prompt = f"""Analyze this website analytics data and provide:

1. KEY INSIGHTS (3-4 bullet points): Identify the most critical findings about performance, user behavior, and growth opportunities. Each insight should be 1-2 sentences.

2. STRATEGIC RECOMMENDATIONS (5-7 items): Provide specific, actionable recommendations with priority levels (Critical/High/Medium). Include the specific metric that needs attention and concrete action to take.

3. ACTION PLAN: Organize actions into:
   - Immediate (This Week): 3-4 urgent actions
   - Short-Term (30 Days): 4-5 strategic actions  
   - Long-Term (Quarter): 3-4 growth initiatives

Use a professional, executive-level tone. Focus on business impact. Include specific numbers from the data.

Data:
{data_summary}

Format your response as JSON with keys: "insights", "recommendations", "action_plan_immediate", "action_plan_short", "action_plan_long". Each recommendation should have: priority, title, description, action."""

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://data-analyst-agent.local",
                    "X-Title": "Data Analyst Agent",
                },
                json={
                    "model": "anthropic/claude-3-haiku",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

                # Try to parse JSON from response
                import re

                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    import json

                    try:
                        ai_data = json.loads(json_match.group())
                        print("✅ AI Insights generated successfully")
                        return ai_data
                    except:
                        pass

            print(f"⚠️ AI generation returned: {response.status_code}")
            return None

        except Exception as e:
            print(f"⚠️ AI insights generation failed: {e}")
            return None

    def _generate_comparison_html(
        self,
        gsc,
        prev_gsc,
        ga4,
        prev_ga4,
        meta,
        prev_meta,
        scores,
        prev_scores,
        prev_start,
        prev_end,
    ) -> str:
        """Generate C-suite style comparison HTML for monthly reports"""

        gsc_clicks = gsc.get("total_clicks", 0)
        prev_gsc_clicks = prev_gsc.get("total_clicks", 0)
        gsc_clicks_diff = gsc_clicks - prev_gsc_clicks
        gsc_clicks_pct = (
            (gsc_clicks_diff / prev_gsc_clicks * 100) if prev_gsc_clicks > 0 else 0
        )

        gsc_impr = gsc.get("total_impressions", 0)
        prev_gsc_impr = prev_gsc.get("total_impressions", 0)
        gsc_impr_diff = gsc_impr - prev_gsc_impr

        gsc_ctr = gsc.get("average_ctr", 0)
        prev_gsc_ctr = prev_gsc.get("average_ctr", 0)

        ga4_sessions = ga4.get("total_sessions", 0)
        prev_ga4_sessions = prev_ga4.get("total_sessions", 0)
        ga4_sessions_diff = ga4_sessions - prev_ga4_sessions
        ga4_sessions_pct = (
            (ga4_sessions_diff / prev_ga4_sessions * 100)
            if prev_ga4_sessions > 0
            else 0
        )

        ga4_users = ga4.get("total_users", 0)
        prev_ga4_users = prev_ga4.get("total_users", 0)

        ga4_bounce = ga4.get("bounce_rate", 0)
        prev_ga4_bounce = prev_ga4.get("bounce_rate", 0)
        bounce_diff = (ga4_bounce - prev_ga4_bounce) * 100

        ga4_conversions = ga4.get("conversions", 0)
        prev_ga4_conversions = prev_ga4.get("conversions", 0)

        meta_impr = meta.get("total_impressions", 0)
        prev_meta_impr = prev_meta.get("total_impressions", 0)
        meta_impr_diff = meta_impr - prev_meta_impr
        meta_impr_pct = (
            (meta_impr_diff / prev_meta_impr * 100) if prev_meta_impr > 0 else 0
        )

        meta_er = meta.get("engagement_rate", 0)
        prev_meta_er = prev_meta.get("engagement_rate", 0)

        overall = scores.get("overall", 0)
        prev_overall = prev_scores.get("overall", 0)
        overall_diff = overall - prev_overall

        def trend_class(val, inverse=False):
            if inverse:
                return (
                    "trend-down"
                    if val > 0
                    else "trend-up"
                    if val < 0
                    else "trend-stable"
                )
            return (
                "trend-up" if val > 0 else "trend-down" if val < 0 else "trend-stable"
            )

        def fmt_num(n):
            return f"{n:,.0f}" if abs(n) >= 100 else f"{n:+.1f}"

        def fmt_pct(p):
            return f"{p:+.1f}%"

        html = f'''
        <div class="exec-summary">
            <h2>Executive Summary - Month over Month Analysis</h2>
            <div style="font-size: 0.9em; margin-bottom: 20px; opacity: 0.9;">
                Current Period vs Previous Period ({prev_start} to {prev_end})
            </div>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{overall:.1f}<span style="font-size: 0.4em;" class="{trend_class(overall_diff)}"> {fmt_pct(overall_diff)}</span></div>
                    <div class="summary-label">Overall Score</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{gsc_clicks:,}<span style="font-size: 0.4em;" class="{trend_class(gsc_clicks_diff)}"> {fmt_pct(gsc_clicks_pct)}</span></div>
                    <div class="summary-label">Search Clicks</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{ga4_sessions:,}<span style="font-size: 0.4em;" class="{trend_class(ga4_sessions_diff)}"> {fmt_pct(ga4_sessions_pct)}</span></div>
                    <div class="summary-label">Web Sessions</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{meta_impr:,}<span style="font-size: 0.4em;" class="{trend_class(meta_impr_diff)}"> {fmt_pct(meta_impr_pct)}</span></div>
                    <div class="summary-label">Social Impressions</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Performance Comparison</h2>
            <div class="grid-2">
                <div class="card">
                    <h2>Search Performance (GSC)</h2>
                    <table style="width:100%; font-size: 0.9em;">
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Metric</td><td style="text-align:right; padding:12px;">Current</td><td style="text-align:right; padding:12px;">Previous</td><td style="text-align:right; padding:12px;">Change</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Clicks</td><td style="text-align:right; padding:12px;">{gsc_clicks:,}</td><td style="text-align:right; padding:12px;">{prev_gsc_clicks:,}</td><td style="text-align:right; padding:12px;" class="{trend_class(gsc_clicks_diff)}">{fmt_pct(gsc_clicks_pct)}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Impressions</td><td style="text-align:right; padding:12px;">{gsc_impr:,}</td><td style="text-align:right; padding:12px;">{prev_gsc_impr:,}</td><td style="text-align:right; padding:12px;">{fmt_num(gsc_impr_diff)}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Avg CTR</td><td style="text-align:right; padding:12px;">{gsc_ctr:.2%}</td><td style="text-align:right; padding:12px;">{prev_gsc_ctr:.2%}</td><td style="text-align:right; padding:12px;">{(gsc_ctr - prev_gsc_ctr) * 100:+.2f}%</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Avg Position</td><td style="text-align:right; padding:12px;">{gsc.get("average_position", 0):.1f}</td><td style="text-align:right; padding:12px;">{prev_gsc.get("average_position", 0):.1f}</td><td style="text-align:right; padding:12px;">{gsc.get("average_position", 0) - prev_gsc.get("average_position", 0):+.1f}</td></tr>
                    </table>
                </div>
                <div class="card">
                    <h2>Web Analytics (GA4)</h2>
                    <table style="width:100%; font-size: 0.9em;">
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Metric</td><td style="text-align:right; padding:12px;">Current</td><td style="text-align:right; padding:12px;">Previous</td><td style="text-align:right; padding:12px;">Change</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Sessions</td><td style="text-align:right; padding:12px;">{ga4_sessions:,}</td><td style="text-align:right; padding:12px;">{prev_ga4_sessions:,}</td><td style="text-align:right; padding:12px;" class="{trend_class(ga4_sessions_diff)}">{fmt_pct(ga4_sessions_pct)}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Users</td><td style="text-align:right; padding:12px;">{ga4_users:,}</td><td style="text-align:right; padding:12px;">{prev_ga4_users:,}</td><td style="text-align:right; padding:12px;">{ga4_users - prev_ga4_users:+d}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Bounce Rate</td><td style="text-align:right; padding:12px;">{ga4_bounce:.1%}</td><td style="text-align:right; padding:12px;">{prev_ga4_bounce:.1%}</td><td style="text-align:right; padding:12px;" class="{trend_class(bounce_diff, True)}">{bounce_diff:+.1f}%</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Conversions</td><td style="text-align:right; padding:12px;">{ga4_conversions}</td><td style="text-align:right; padding:12px;">{prev_ga4_conversions}</td><td style="text-align:right; padding:12px;">{ga4_conversions - prev_ga4_conversions:+d}</td></tr>
                    </table>
                </div>
            </div>
            <div class="grid-2" style="margin-top: 20px;">
                <div class="card">
                    <h2>Social Media (Meta)</h2>
                    <table style="width:100%; font-size: 0.9em;">
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Metric</td><td style="text-align:right; padding:12px;">Current</td><td style="text-align:right; padding:12px;">Previous</td><td style="text-align:right; padding:12px;">Change</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Impressions</td><td style="text-align:right; padding:12px;">{meta_impr:,}</td><td style="text-align:right; padding:12px;">{prev_meta_impr:,}</td><td style="text-align:right; padding:12px;" class="{trend_class(meta_impr_diff)}">{fmt_pct(meta_impr_pct)}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Engagement Rate</td><td style="text-align:right; padding:12px;">{meta_er:.2%}</td><td style="text-align:right; padding:12px;">{prev_meta_er:.2%}</td><td style="text-align:right; padding:12px;">{(meta_er - prev_meta_er) * 100:+.2f}%</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Page Fans</td><td style="text-align:right; padding:12px;">{meta.get("total_fans", 0):,}</td><td style="text-align:right; padding:12px;">{prev_meta.get("total_fans", 0):,}</td><td style="text-align:right; padding:12px;">{meta.get("total_fans", 0) - prev_meta.get("total_fans", 0):+d}</td></tr>
                    </table>
                </div>
                <div class="card">
                    <h2>Executive Scorecard</h2>
                    <table style="width:100%; font-size: 0.9em;">
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Score</td><td style="text-align:right; padding:12px;">Current</td><td style="text-align:right; padding:12px;">Previous</td><td style="text-align:right; padding:12px;">Change</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Overall</td><td style="text-align:right; padding:12px;"><strong>{overall:.1f}</strong></td><td style="text-align:right; padding:12px;"><strong>{prev_overall:.1f}</strong></td><td style="text-align:right; padding:12px;" class="{trend_class(overall_diff)}"><strong>{fmt_pct(overall_diff)}</strong></td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Search Visibility</td><td style="text-align:right; padding:12px;">{scores.get("search_visibility", 0):.1f}</td><td style="text-align:right; padding:12px;">{prev_scores.get("search_visibility", 0):.1f}</td><td style="text-align:right; padding:12px;">{scores.get("search_visibility", 0) - prev_scores.get("search_visibility", 0):+.1f}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">GA4 Performance</td><td style="text-align:right; padding:12px;">{scores.get("ga4_performance", 0):.1f}</td><td style="text-align:right; padding:12px;">{prev_scores.get("ga4_performance", 0):.1f}</td><td style="text-align:right; padding:12px;">{scores.get("ga4_performance", 0) - prev_scores.get("ga4_performance", 0):+.1f}</td></tr>
                        <tr style="border-bottom: 1px solid #eee;"><td style="padding:12px;">Meta Performance</td><td style="text-align:right; padding:12px;">{scores.get("meta_performance", 0):.1f}</td><td style="text-align:right; padding:12px;">{prev_scores.get("meta_performance", 0):.1f}</td><td style="text-align:right; padding:12px;">{scores.get("meta_performance", 0) - prev_scores.get("meta_performance", 0):+.1f}</td></tr>
                    </table>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Key Takeaways & Executive Summary</h2>
            {self._generate_takeaways(gsc, prev_gsc, ga4, prev_ga4, meta, prev_meta, scores, prev_scores)}
        </div>
        '''
        return html

    def _generate_takeaways(
        self, gsc, prev_gsc, ga4, prev_ga4, meta, prev_meta, scores, prev_scores
    ) -> str:
        """Generate executive takeaways based on comparison"""
        takeaways = []

        gsc_diff = gsc.get("total_clicks", 0) - prev_gsc.get("total_clicks", 0)
        if gsc_diff > 0:
            takeaways.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Positive Trend:</strong> Search clicks increased by {gsc_diff} (+{(gsc_diff / max(prev_gsc.get("total_clicks", 1), 1)) * 100:.1f}%) compared to previous month.
            </div>""")
        elif gsc_diff < 0:
            takeaways.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Attention Needed:</strong> Search clicks decreased by {abs(gsc_diff)} ({abs(gsc_diff) / max(prev_gsc.get("total_clicks", 1), 1) * 100:.1f}%) compared to previous month. Review SEO strategy.
            </div>""")

        ga4_diff = ga4.get("total_sessions", 0) - prev_ga4.get("total_sessions", 0)
        if ga4_diff > 0:
            takeaways.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Growth:</strong> Web traffic increased by {ga4_diff} sessions (+{(ga4_diff / max(prev_ga4.get("total_sessions", 1), 1)) * 100:.1f}%) month-over-month.
            </div>""")

        bounce_change = ga4.get("bounce_rate", 0) - prev_ga4.get("bounce_rate", 0)
        if bounce_change < -0.05:
            takeaways.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Improved Engagement:</strong> Bounce rate improved by {abs(bounce_change) * 100:.1f} percentage points, indicating better user engagement.
            </div>""")
        elif bounce_change > 0.05:
            takeaways.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Engagement Warning:</strong> Bounce rate increased by {bounce_change * 100:.1f} percentage points. Investigate user experience issues.
            </div>""")

        conv_curr = ga4.get("conversions", 0)
        conv_prev = prev_ga4.get("conversions", 0)
        if conv_curr > conv_prev:
            takeaways.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Conversion Growth:</strong> Conversions increased from {conv_prev} to {conv_curr} (+{conv_curr - conv_prev}).
            </div>""")
        elif conv_curr == 0 and conv_prev == 0:
            takeaways.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Critical Gap:</strong> No conversions tracked in either period. Immediate action required.
            </div>""")

        meta_diff = meta.get("total_impressions", 0) - prev_meta.get(
            "total_impressions", 0
        )
        if meta_diff > 0:
            takeaways.append(f"""<div class="insight" style="border-left-color: #0d6efd;">
                <strong>Social Growth:</strong> Social media impressions increased by {(meta_diff / max(prev_meta.get("total_impressions", 1), 1)) * 100:.1f}%.
            </div>""")

        overall_diff = scores.get("overall", 0) - prev_scores.get("overall", 0)
        if overall_diff > 2:
            takeaways.append(f"""<div class="insight" style="border-left-color: #198754;">
                <strong>Overall Improvement:</strong> Overall performance score improved by {overall_diff:.1f} points. Strong momentum.
            </div>""")
        elif overall_diff < -2:
            takeaways.append(f"""<div class="insight" style="border-left-color: #dc3545;">
                <strong>Performance Decline:</strong> Overall score dropped by {abs(overall_diff):.1f} points. Review all channels.
            </div>""")

        return (
            "\n".join(takeaways)
            if takeaways
            else '<div class="insight">No significant changes detected between periods.</div>'
        )

    def _generate_ai_html_insights(
        self, ai_insights: Dict, gsc: Dict, ga4: Dict, meta: Dict, scores: Dict
    ) -> str:
        """Generate HTML for AI-powered insights"""
        if not ai_insights:
            return self._generate_dynamic_insights(gsc, ga4, meta, scores)

        insights_html = ""

        # Add AI-generated insights
        if "insights" in ai_insights:
            for i, insight in enumerate(ai_insights.get("insights", [])):
                color = (
                    "#198754"
                    if i == 0
                    else "#0d6efd"
                    if i == 1
                    else "#ffc107"
                    if i == 2
                    else "#7a7a7a"
                )
                insights_html += f"""<div class="insight" style="border-left-color: {color};">
                    {insight}
                </div>"""

        # Add AI-generated recommendations
        if "recommendations" in ai_insights:
            for rec in ai_insights.get("recommendations", []):
                priority = rec.get("priority", "Medium").lower()
                priority_class = (
                    "high"
                    if priority in ["critical", "high"]
                    else "growth"
                    if priority == "growth"
                    else ""
                )
                color = (
                    "#dc3545"
                    if priority == "critical"
                    else "#ffc107"
                    if priority == "high"
                    else "#198754"
                )
                insights_html += f"""<div class="recommendation {priority_class}" style="border-left-color: {color};">
                    <div class="rec-priority">{rec.get("priority", "Medium").upper()} PRIORITY</div>
                    <div class="rec-title">{rec.get("title", "")}</div>
                    <div class="rec-desc">{rec.get("description", "")}</div>
                    <div class="rec-action"><strong>Recommended Action:</strong> {rec.get("action", rec.get("description", ""))}</div>
                </div>"""

        return insights_html

    def _get_gsc_recommendations(self, gsc: Dict) -> List[Dict]:
        """Generate GSC-specific recommendations"""
        recs = []
        if gsc.get("average_position", 0) > 5:
            recs.append(
                {
                    "priority": "High",
                    "title": "Improve Search Rankings",
                    "description": f"Average position is {gsc.get('average_position', 0):.1f}. Focus on content optimization and building backlinks to reach top 3.",
                }
            )
        if gsc.get("average_ctr", 0) < 0.03:
            recs.append(
                {
                    "priority": "High",
                    "title": "Improve CTR",
                    "description": f"CTR is {gsc.get('average_ctr', 0):.2%}. Optimize title tags and meta descriptions with power words.",
                }
            )
        if gsc.get("positions_4_10", 0) > 0:
            recs.append(
                {
                    "priority": "Medium",
                    "title": "Optimize Page 1 Keywords",
                    "description": f"{gsc.get('positions_4_10', 0)} queries ranking 4-10. Small improvements can boost these to top 3.",
                }
            )
        if not recs:
            recs.append(
                {
                    "priority": "Low",
                    "title": "Maintain Performance",
                    "description": "SEO metrics look good. Continue current strategy and monitor trends.",
                }
            )
        return recs

    def _get_ga4_recommendations(self, ga4: Dict) -> List[Dict]:
        """Generate GA4-specific recommendations"""
        recs = []
        if ga4.get("bounce_rate", 0) > 0.5:
            recs.append(
                {
                    "priority": "High",
                    "title": "Reduce Bounce Rate",
                    "description": f"Bounce rate is {ga4.get('bounce_rate', 0):.1%}. Improve page speed, add engaging content, and ensure mobile responsiveness.",
                }
            )
        if ga4.get("conversions", 0) == 0:
            recs.append(
                {
                    "priority": "High",
                    "title": "Set Up Conversions",
                    "description": "No conversions tracked. Set up conversion events in GA4 for key actions (signups, purchases, form submissions).",
                }
            )
        if ga4.get("total_sessions", 0) < 100:
            recs.append(
                {
                    "priority": "Medium",
                    "title": "Increase Traffic",
                    "description": f"Only {ga4.get('total_sessions', 0)} sessions. Improve SEO and consider paid traffic to increase visitors.",
                }
            )
        if not recs:
            recs.append(
                {
                    "priority": "Low",
                    "title": "Maintain Performance",
                    "description": "Web analytics look healthy. Continue monitoring and optimizing.",
                }
            )
        return recs

    def _get_meta_recommendations(self, meta: Dict) -> List[Dict]:
        """Generate Meta-specific recommendations"""
        recs = []
        if meta.get("engagement_rate", 0) < 0.03:
            recs.append(
                {
                    "priority": "High",
                    "title": "Boost Engagement",
                    "description": f"Engagement rate is {meta.get('engagement_rate', 0):.2%}. Post more videos, use polls, and ask questions.",
                }
            )
        if meta.get("total_impressions", 0) < 10000:
            recs.append(
                {
                    "priority": "Medium",
                    "title": "Increase Reach",
                    "description": "Low impressions. Post more consistently and use relevant hashtags.",
                }
            )
        recs.append(
            {
                "priority": "Medium",
                "title": "Content Strategy",
                "description": "Mix of content types: educational posts, behind-the-scenes, customer testimonials, and promotional content.",
            }
        )
        if not recs:
            recs.append(
                {
                    "priority": "Low",
                    "title": "Maintain Performance",
                    "description": "Social metrics look good. Continue engaging with your audience.",
                }
            )
        return recs


def main():
    """Main entry point"""
    import calendar as cal
    from datetime import timedelta

    # Check for scheduled analysis
    if "--schedule" in sys.argv:
        try:
            schedule_idx = sys.argv.index("--schedule")
            schedule = (
                sys.argv[schedule_idx + 1]
                if schedule_idx + 1 < len(sys.argv)
                else "daily"
            )
        except:
            schedule = "daily"

        # Get website URL from args or use default
        site_url = "https://www.skinessentialsbyher.com"
        if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
            site_url = sys.argv[2]

        analyst = DataAnalyst()
        analyst.run_scheduled_analysis(site_url, schedule)
        return

    # Check for report type
    report_type = "standard"  # default
    if "--report" in sys.argv:
        try:
            report_type = sys.argv[sys.argv.index("--report") + 1]
        except:
            report_type = "standard"

    if len(sys.argv) < 2:
        print(
            "Usage: python data_analyst.py <website_url> [--days 30] [--channels gsc,ga4,meta] [--report standard|weekly|monthly]\n"
            "       python data_analyst.py --schedule daily [website_url]"
        )
        print("\nExamples:")
        print("  python data_analyst.py https://example.com")
        print(
            "  python data_analyst.py https://example.com --days 30 --channels gsc,ga4"
        )
        print("  python data_analyst.py https://example.com --report weekly")
        print("  python data_analyst.py https://example.com --report monthly")
        print("  python data_analyst.py --schedule weekly")
        print("  python data_analyst.py --schedule monthly")
        sys.exit(1)

    site_url = sys.argv[1]
    days = 30
    channels = ["gsc", "ga4", "meta"]
    comparison_data = None

    # Handle different report types
    if report_type == "weekly":
        # Monday to Saturday of current week
        today = datetime.now()
        # Find Monday of current week
        monday = today - timedelta(days=today.weekday())
        # Saturday is monday + 5 days
        saturday = monday + timedelta(days=5)
        start_date = monday.strftime("%Y-%m-%d")
        end_date = saturday.strftime("%Y-%m-%d")
        days = (saturday - monday).days + 1
        print(f"Weekly Report: {start_date} to {end_date}")

    elif report_type == "monthly" or report_type == "monthly-running":
        # Current month with comparison to previous month
        today = datetime.now()
        first_day_current = today.replace(day=1)

        if report_type == "monthly-running":
            # Monthly Running: 1st of month to TODAY (not end of month)
            last_day_current = today
            print(
                f"Monthly Running Report: {first_day_current.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')} (Current month to date)"
            )
        else:
            # Full Monthly: 1st of month to end of month
            last_day_current = today.replace(
                day=cal.monthrange(today.year, today.month)[1]
            )
            print(
                f"Monthly Report: {first_day_current.strftime('%Y-%m-%d')} to {last_day_current.strftime('%Y-%m-%d')} (Full month)"
            )

        # Previous month (same number of days as current period)
        if today.month == 1:
            first_day_prev = today.replace(year=today.year - 1, month=12, day=1)
        else:
            first_day_prev = today.replace(month=today.month - 1, day=1)

        # Previous period has same number of days
        days_in_period = (last_day_current - first_day_current).days + 1
        last_day_prev = first_day_prev + timedelta(days=days_in_period - 1)

        start_date = first_day_current.strftime("%Y-%m-%d")
        end_date = last_day_current.strftime("%Y-%m-%d")
        prev_start = first_day_prev.strftime("%Y-%m-%d")
        prev_end = last_day_prev.strftime("%Y-%m-%d")

        days = days_in_period
        print(f"Comparison Period: {prev_start} to {prev_end}")

    else:
        # Standard report
        if "--days" in sys.argv:
            try:
                days = int(sys.argv[sys.argv.index("--days") + 1])
            except (ValueError, IndexError):
                pass

        # Custom date range
        start_date = None
        end_date = None
        if "--start" in sys.argv:
            try:
                start_date = sys.argv[sys.argv.index("--start") + 1]
            except (ValueError, IndexError):
                pass
        if "--end" in sys.argv:
            try:
                end_date = sys.argv[sys.argv.index("--end") + 1]
            except (ValueError, IndexError):
                pass

        # Override days if custom dates provided
        if start_date and end_date:
            days = None  # Will be calculated from dates

    if "--channels" in sys.argv:
        try:
            channels_str = sys.argv[sys.argv.index("--channels") + 1]
            channels = [c.strip() for c in channels_str.split(",")]
        except (ValueError, IndexError):
            pass

    analyst = DataAnalyst()

    # Test API connections first
    print("\n" + "=" * 60)
    print("🔌 TESTING API CONNECTIONS")
    print("=" * 60)

    gsc_ok = analyst.authenticate_gsc()
    ga4_ok = analyst.authenticate_ga4()
    meta_ok = analyst.authenticate_meta()

    print("\n" + "=" * 60)
    print("📡 CONNECTION STATUS")
    print("=" * 60)
    print(
        f"{'✓' if gsc_ok else '✗'} Google Search Console: {'Connected' if gsc_ok else 'FAILED'}"
    )
    print(
        f"{'✓' if ga4_ok else '✗'} Google Analytics 4:  {'Connected' if ga4_ok else 'FAILED'}"
    )
    print(
        f"{'✓' if meta_ok else '✗'} Meta/Facebook:     {'Connected' if meta_ok else 'FAILED'}"
    )

    if not gsc_ok and not ga4_ok and not meta_ok:
        print("\n❌ All API connections failed. Please check credentials.")
        sys.exit(1)

    if not gsc_ok:
        print("\n⚠️  Warning: GSC not connected - search data will be unavailable")
    if not ga4_ok:
        print("\n⚠️  Warning: GA4 not connected - web analytics will be unavailable")
    if not meta_ok:
        print("\n⚠️  Warning: Meta not connected - social data will be unavailable")

    print("\n" + "=" * 60)

    analyst.set_site(site_url)

    # Generate report for current period
    report = analyst.generate_unified_report(
        site_url, days, channels, start_date, end_date
    )

    # If monthly or monthly-running, also get previous month data for comparison
    if (
        (report_type == "monthly" or report_type == "monthly-running")
        and start_date
        and end_date
    ):
        print("Fetching previous month data for comparison...")
        prev_report = analyst.generate_unified_report(
            site_url, days, channels, prev_start, prev_end
        )
        comparison_data = {
            "previous": prev_report,
            "prev_start": prev_start,
            "prev_end": prev_end,
        }
        print(f"Previous period: {prev_start} to {prev_end}")

    if report:
        # Save to historical data
        analyst.save_historical_data(site_url, report)

        output_file = f"data_report_{site_url.replace('https://', '').replace('http://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        analyst.export_report(report, output_file)

        # Get trends and recommendations
        trends = analyst.analyze_trends(site_url)
        growth_recs = analyst.generate_growth_recommendations(site_url, trends)

        # Generate HTML dashboard with comparison if monthly
        site_name = (
            site_url.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .replace("/", "")
        )
        html_dashboard_file = (
            f"dashboard_{site_name}_{datetime.now().strftime('%Y%m%d')}.html"
        )
        analyst.export_html_dashboard(
            report,
            html_dashboard_file,
            trends,
            growth_recs,
            comparison_data,
            report_type,
            start_date,
            end_date,
            days,
        )

        # Copy HTML to Desktop folder
        import shutil

        desktop_report_dir = os.path.expanduser(
            f"~/Desktop/data-analyst/{site_name}-reports"
        )
        os.makedirs(desktop_report_dir, exist_ok=True)

        # Determine report filename based on type
        if report_type == "weekly":
            report_filename = f"weekly-report-{start_date}-to-{end_date}.html"
        elif report_type == "monthly":
            report_filename = f"monthly-report-{start_date}-to-{end_date}.html"
        else:
            report_filename = f"dashboard-{datetime.now().strftime('%Y%m%d')}.html"

        desktop_html_path = os.path.join(desktop_report_dir, report_filename)
        shutil.copy2(html_dashboard_file, desktop_html_path)
        print(f"\n📁 Report saved to Desktop: {desktop_html_path}")

        # Also generate Streamlit dashboard for interactive use
        st_dashboard_file = (
            f"dashboard_{site_name}_{datetime.now().strftime('%Y%m%d')}.py"
        )
        analyst.export_streamlit_dashboard(
            report, st_dashboard_file, trends, growth_recs
        )

        # Also generate a consistent "latest" dashboard that can always be run
        latest_dashboard = "dashboard_latest.py"
        analyst.export_streamlit_dashboard(
            report, latest_dashboard, trends, growth_recs
        )
        print(f"✅ Latest dashboard saved to: {latest_dashboard}")
        print(f"   Run with: streamlit run {latest_dashboard}")

        # Print growth recommendations
        print("\n" + "=" * 60)
        print("📈 GROWTH RECOMMENDATIONS")
        print("=" * 60)
        for i, rec in enumerate(growth_recs[:5], 1):
            print(
                f"\n{i}. [{rec.get('priority', 'Medium').upper()}] {rec.get('title', '')}"
            )
            print(f"   {rec.get('description', '')}")
            print(f"   ➡️ Action: {rec.get('action', '')}")

        # Run Streamlit dashboard instead of HTML
        import subprocess

        print("\n🚀 Opening Streamlit dashboard...")
        st_dashboard_path = os.path.abspath(st_dashboard_file)

        # Run streamlit in headless mode (no browser auto-open, but server starts)
        subprocess.Popen(
            [
                "streamlit",
                "run",
                st_dashboard_path,
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        print(f"   Streamlit dashboard starting at: http://localhost:8501")
        print(f"   Dashboard file: {st_dashboard_path}")

        # Generate LLM prompt file
        desktop_prompt_dir = os.path.expanduser(f"~/Desktop/analytics/{site_name}")
        os.makedirs(desktop_prompt_dir, exist_ok=True)

        # Get data from report
        report_channels = report.get("channels", {})
        report_scores = report.get("scores", {})

        # Create filled prompt
        gsc_data = f"Total Clicks: {report_channels.get('gsc', {}).get('total_clicks', 0)}\nTotal Impressions: {report_channels.get('gsc', {}).get('total_impressions', 0)}\nAvg CTR: {report_channels.get('gsc', {}).get('average_ctr', 0):.2%}\nAvg Position: {report_channels.get('gsc', {}).get('average_position', 0):.1f}"
        ga4_data = f"Total Sessions: {report_channels.get('ga4', {}).get('total_sessions', 0)}\nTotal Users: {report_channels.get('ga4', {}).get('total_users', 0)}\nBounce Rate: {report_channels.get('ga4', {}).get('bounce_rate', 0):.1%}\nConversions: {report_channels.get('ga4', {}).get('conversions', 0)}"
        meta_data = f"Total Impressions: {report_channels.get('meta', {}).get('total_impressions', 0):,}\nEngaged Users: {report_channels.get('meta', {}).get('total_engaged_users', 0):,}\nPage Fans: {report_channels.get('meta', {}).get('total_fans', 0):,}\nEngagement Rate: {report_channels.get('meta', {}).get('engagement_rate', 0):.2%}"

        prompt_content = f"""# Analytics Report - LLM Action Prompt

You are a senior digital marketing strategist. Analyze the following website analytics data and provide actionable recommendations.

## Report Details
- **Website**: {site_url}
- **Report Type**: {report_type}
- **Period**: {start_date} to {end_date}
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **Author**: Vincent John Rodriguez

---

## Current Performance Data

### Google Search Console (GSC) - Search Performance
```
{gsc_data}
```

### Google Analytics 4 (GA4) - Web Analytics
```
{ga4_data}
```

### Meta/Facebook - Social Performance
```
{meta_data}
```

### Overall Scores
- **Overall Score**: {report_scores.get("overall", 0):.1f}/100
- **Search Visibility**: {report_scores.get("search_visibility", 0):.1f}/100
- **GA4 Performance**: {report_scores.get("ga4_performance", 0):.1f}/100
- **Meta Performance**: {report_scores.get("meta_performance", 0):.1f}/100

---

## Your Task

Based on the analytics data above, create a comprehensive **Strategic Action Plan** with the following sections:

### 1. Executive Summary (3-4 sentences)
Brief overview of current performance and key priority areas.

### 2. Critical Issues (Immediate Action Required)
List the top 3 issues that need immediate attention within 7 days.
For each issue:
- **Issue**: Description
- **Impact**: Why this matters
- **Action**: Specific step to take

### 3. Short-Term Improvements (30 Days)
List 5 specific actions to improve performance in the next 30 days.
For each:
- **Action**: Specific task
- **Expected Impact**: What metric will improve
- **Effort**: Low/Medium/High

### 4. Long-Term Strategy (Quarterly)
List 3-4 strategic initiatives for the next quarter.
For each:
- **Initiative**: Description
- **Resources Needed**: What you need
- **Success Metric**: How to measure

### 5. Quick Wins
List 3-5 quick wins that can be implemented immediately with minimal effort.

---

## Important Guidelines

1. **Be Specific**: Don't say "improve SEO" - say "optimize title tags for keywords X, Y, Z"
2. **Prioritize**: Focus on highest impact items first
3. **Be Realistic**: Consider the data - if bounce rate is 70%, focus on user experience
4. **No Emojis**: Use professional language
5. **Data-Driven**: Reference specific numbers from the report

---

## Output Format

Provide your response in clean markdown format with clear headings. Do not use bullet emojis. Use dashes or numbers instead.

Begin your analysis now.
"""

        # Save prompt file
        prompt_filename = f"llm-prompt-{start_date}-to-{end_date}.md"
        prompt_path = os.path.join(desktop_prompt_dir, prompt_filename)
        with open(prompt_path, "w") as f:
            f.write(prompt_content)

        print(f"📝 LLM Prompt saved to: {prompt_path}")


if __name__ == "__main__":
    main()
