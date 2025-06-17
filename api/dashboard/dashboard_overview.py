from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc
from datetime import datetime
from collections import Counter
from models.models import URL, Click
from database.db import get_session
from schemas.dashboard import SummaryData, RecentClick, URLData
from utils.dashboard import get_ttl_and_status, format_time_diff
from utils.colors import COLOR_MAP
from typing import List, Optional

router = APIRouter()


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    user_id: str = Query(...), session: AsyncSession = Depends(get_session)
):
    try:
        # OPTIMIZATION 1: Single query to load all URLs with their clicks
        # This replaces multiple separate queries and eliminates N+1 query problem
        result = await session.execute(
            select(URL).options(selectinload(URL.clicks)).where(URL.user_id == user_id)
        )
        urls = result.scalars().all()

        # OPTIMIZATION 2: Extract all clicks once and reuse for multiple calculations
        # This eliminates redundant iterations and separate queries
        all_clicks = []
        for url in urls:
            for click in url.clicks:
                all_clicks.append((click, url.short_code))

        # Sort clicks by timestamp (most recent first) for reuse
        all_clicks.sort(key=lambda x: x[0].timestamp, reverse=True)

        # 1. Summary Data - calculated from preloaded data
        total_urls = len(urls)
        protected_urls = sum(1 for u in urls if u.is_protected)
        total_clicks = len(all_clicks)

        # 2. Most Recent Click - OPTIMIZED: use already loaded data instead of separate query
        recent = None
        if all_clicks:
            recent_click = all_clicks[0][0]  # First item is most recent
            recent = RecentClick(
                time=format_time_diff(recent_click.timestamp),
                country=recent_click.country or "Unknown",
                flag=recent_click.flag or "🏳️",
            )

        # 3. URL Table Data - reuse preloaded data
        url_list: List[URLData] = [
            URLData(
                id=str(u.id),
                shortUrl=f"redirecto/{u.short_code}",
                destination=u.destination,
                clicks=len(u.clicks),
                ttl=get_ttl_and_status(u.expires_at)[0],
                status=get_ttl_and_status(u.expires_at)[1],
                protected=u.is_protected,
                createdAt=u.created_at.strftime("%Y-%m-%d"),
            )
            for u in urls
        ]

        # 4. Country Data - OPTIMIZED: calculate from already loaded clicks instead of separate query
        country_counter = Counter(click.country or "Others" for click, _ in all_clicks)
        country_data = [
            {
                "country": country,
                "clicks": count,
                "color": COLOR_MAP.get(country, "#f59e0b"),
            }
            for country, count in country_counter.items()
        ]

        # 5. Clicks Over Time - OPTIMIZED: calculate from loaded data, but keep query for date truncation
        # Note: This still requires a query because we need database-level date truncation
        # However, we could potentially optimize this further if needed
        clicks_over_time_query = await session.execute(
            select(
                func.date_trunc("day", Click.timestamp).label("day"),
                func.count(Click.id),
            )
            .join(URL)
            .where(URL.user_id == user_id)
            .group_by("day")
            .order_by(desc("day"))
            .limit(7)
        )

        clicks_over_time = [
            {"day": row[0].strftime("%a"), "clicks": row[1]}
            for row in reversed(clicks_over_time_query.all())
        ]

        # 6. Recent Activity - OPTIMIZED: use already sorted clicks data instead of separate query
        recent_activity = []
        for click, short_code in all_clicks[:5]:  # Take first 5 (most recent)
            recent_activity.append(
                {
                    "id": str(click.id),
                    "shortUrl": f"redirecto/{short_code}",
                    "country": click.country or "Unknown",
                    "flag": click.flag or "🏳️",
                    "time": format_time_diff(click.timestamp),
                }
            )

        return {
            "summary": SummaryData(
                totalUrls=total_urls,
                totalClicks=total_clicks,
                protectedUrls=protected_urls,
                recentClick=recent,
            ),
            "urls": url_list,
            "countryData": country_data,
            "clicksOverTime": clicks_over_time,
            "recentActivity": recent_activity,
        }

    except Exception as e:
        print(f"Error fetching dashboard for user_id={user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")
