import httpx
from fastapi import Request


def country_code_to_flag_emoji(code: str) -> str:
    """
    Convert country code (e.g. 'IN') to flag emoji 🇮🇳
    """
    return "".join(chr(127397 + ord(c)) for c in code.upper())


async def get_country_and_flag(request: Request) -> tuple[str, str]:
    """
    Fetch user's country name and flag using ipapi.co
    """
    try:
        client_ip = request.client.host
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ipapi.co/{client_ip}/json/")
            if response.status_code == 200:
                data = response.json() if response.is_success else {}
                country = data.get("country_name", "Unknown")
                code = data.get("country_code", "")
                flag = country_code_to_flag_emoji(code) if code else "🏳️"
                return country, flag
    except Exception as e:
        print(f"GeoIP fetch failed: {e}")

    return "Unknown", "🏳️"
