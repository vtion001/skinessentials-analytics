"""
Data Analyst API Server

FastAPI server that exposes the Data Analyst agent as REST endpoints.
Supports both JSON API and generative UI integration.

Usage:
    python api_server.py
    # Server runs on http://localhost:8000

Endpoints:
    - GET  /api/health          - Health check
    - POST /api/analyze         - Run analysis, returns JSON
    - GET  /api/report/{site}   - Get latest report for site
    - GET  /api/trends/{site}   - Get trend analysis
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_analyst import DataAnalyst


class Settings(BaseSettings):
    """API Settings"""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]

    # Data Analyst credentials
    gsc_credentials_path: str = "service-account.json"
    ga4_credentials_path: str = "service-account.json"
    ga4_property_id: str = ""
    meta_access_token: str = ""
    meta_app_id: str = ""
    meta_page_id: str = ""
    openrouter_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class AnalyzeRequest(BaseModel):
    """Request model for analysis"""

    website_url: str = Field(..., description="Website URL to analyze")
    days: int = Field(30, description="Number of days to analyze")
    channels: List[str] = Field(
        ["gsc", "ga4", "meta"], description="Channels to analyze"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "website_url": "https://example.com",
                "days": 30,
                "channels": ["gsc", "ga4", "meta"],
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for analysis"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    report_id: Optional[str] = None
    generated_at: Optional[str] = None


app = FastAPI(
    title="Data Analyst API",
    description="REST API for Multi-Channel Data Analysis Agent",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
settings = Settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for reports (in production, use a database)
reports_store: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Data Analyst API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "analyze": "POST /api/analyze",
            "report": "GET /api/report/{site}",
            "trends": "GET /api/trends/{site}",
        },
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "data-analyst-api",
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_site(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze a website and return comprehensive report.

    This endpoint:
    1. Runs the Data Analyst agent
    2. Returns JSON data for integration with generative UI
    3. Stores report for later retrieval
    """
    try:
        # Initialize the analyst
        analyst = DataAnalyst()

        # Authenticate with available APIs
        analyst.authenticate_gsc()
        analyst.authenticate_ga4()
        analyst.authenticate_meta()

        # Set the site
        analyst.set_site(request.website_url)

        # Generate the report
        channels_str = ",".join(request.channels)
        report = analyst.generate_unified_report(
            site_url=request.website_url, days=request.days, channels=request.channels
        )

        if not report:
            return AnalysisResponse(
                success=False, message="Analysis failed - no data returned", data=None
            )

        # Analyze trends
        trends = analyst.analyze_trends(request.website_url)

        # Generate recommendations
        recommendations = analyst.generate_growth_recommendations(
            request.website_url, trends
        )

        # Add trends and recommendations to report
        report["trends"] = trends
        report["recommendations"] = recommendations

        # Generate a report ID
        site_name = (
            request.website_url.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .split("/")[0]
        )
        report_id = f"{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Store the report
        reports_store[report_id] = report
        reports_store[site_name] = report  # Also store by site name for easy retrieval

        # Save to file
        analyst.save_historical_data(request.website_url, report)

        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            data=report,
            report_id=report_id,
            generated_at=report.get("generated_at"),
        )

    except Exception as e:
        return AnalysisResponse(
            success=False, message=f"Analysis failed: {str(e)}", data=None
        )


@app.get("/api/report/{site}")
async def get_report(site: str):
    """
    Get the latest report for a site.

    Args:
        site: Site domain (e.g., "example.com")
    """
    if site not in reports_store:
        # Try to load from file
        site_clean = (
            site.replace("https://", "").replace("http://", "").replace("www.", "")
        )
        history_file = Path(__file__).parent / "history" / f"history_{site_clean}.json"

        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
                    if history:
                        # Return the most recent
                        return {
                            "success": True,
                            "data": history[-1]["report"],
                            "site": site,
                        }
            except Exception:
                pass

        raise HTTPException(status_code=404, detail=f"No report found for site: {site}")

    return {"success": True, "data": reports_store[site], "site": site}


@app.get("/api/trends/{site}")
async def get_trends(site: str):
    """
    Get trend analysis for a site.

    Args:
        site: Site domain
    """
    # Load historical data
    site_clean = site.replace("https://", "").replace("http://", "").replace("www.", "")
    history_file = Path(__file__).parent / "history" / f"history_{site_clean}.json"

    if not history_file.exists():
        raise HTTPException(
            status_code=404, detail=f"No historical data found for: {site}"
        )

    try:
        with open(history_file, "r") as f:
            history = json.load(f)

        if len(history) < 2:
            return {
                "success": False,
                "message": "Need at least 2 reports for trend analysis",
                "data": None,
            }

        # Calculate trends
        analyst = DataAnalyst()
        trends = analyst.analyze_trends(site)

        return {"success": True, "data": trends, "history_count": len(history)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating trends: {str(e)}"
        )


@app.get("/api/sites")
async def list_sites():
    """List all available sites with reports"""
    sites = []

    # Check history directory
    history_dir = Path(__file__).parent / "history"
    if history_dir.exists():
        for file in history_dir.glob("history_*.json"):
            site_name = file.stem.replace("history_", "")
            sites.append(site_name)

    return {"success": True, "sites": sites, "count": len(sites)}


@app.delete("/api/report/{report_id}")
async def delete_report(report_id: str):
    """Delete a specific report"""
    if report_id in reports_store:
        del reports_store[report_id]
        return {"success": True, "message": f"Report {report_id} deleted"}

    raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")


# ==================== GENERATIVE UI SUPPORT ====================


@app.get("/api/ui/overview")
async def get_ui_overview():
    """
    Simplified endpoint for generative UI.
    Returns essential metrics in a format optimized for UI generation.
    """
    # Get all available sites
    sites = list(reports_store.keys())

    if not sites:
        return {
            "success": True,
            "data": {
                "hasData": False,
                "message": "No reports available. Run /api/analyze first.",
            },
        }

    # Get the most recent report
    latest_site = list(reports_store.keys())[-1]
    report = reports_store[latest_site]

    scores = report.get("scores", {})
    channels = report.get("channels", {})
    gsc = channels.get("gsc", {})
    ga4 = channels.get("ga4", {})
    meta = channels.get("meta", {})

    return {
        "success": True,
        "data": {
            "hasData": True,
            "site": latest_site,
            "overallScore": scores.get("overall", 0),
            "searchClicks": gsc.get("total_clicks", 0),
            "webSessions": ga4.get("total_sessions", 0),
            "socialImpressions": meta.get("total_impressions", 0),
            "bounceRate": ga4.get("bounce_rate", 0),
            "engagement": meta.get("engagement_rate", 0),
            "scores": scores,
            "channels": {"search": gsc, "web": ga4, "social": meta},
        },
    }


@app.get("/api/ui/channels/{channel}")
async def get_ui_channel(channel: str):
    """
    Get channel-specific data for generative UI.

    Args:
        channel: One of "search", "web", "social"
    """
    # Get the most recent report
    if not reports_store:
        raise HTTPException(status_code=404, detail="No reports available")

    latest_key = list(reports_store.keys())[-1]
    report = reports_store[latest_key]

    channel_map = {"search": "gsc", "web": "ga4", "social": "meta"}

    channel_key = channel_map.get(channel.lower())
    if not channel_key:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel: {channel}. Use: search, web, or social",
        )

    channel_data = report.get("channels", {}).get(channel_key, {})

    return {"success": True, "channel": channel, "data": channel_data}


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("📊 Data Analyst API Server")
    print("=" * 60)
    print(f"🚀 Starting server on http://{settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
    print("=" * 60)

    uvicorn.run(app, host=settings.host, port=settings.port, reload=True)
