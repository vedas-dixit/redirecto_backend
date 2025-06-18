import httpx
from fastapi import Request


def country_code_to_flag_emoji(code: str) -> str:
    """
    Convert country code (e.g. 'IN') to flag emoji 🇮🇳
    """
    return "".join(chr(127397 + ord(c)) for c in code.upper())

def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP address from the request.
    """
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # This may contain multiple IPs: "client, proxy1, proxy2"
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host  # fallback

async def get_country_and_flag(request: Request) -> tuple[str, str]:
    try:
        client_ip = get_client_ip(request)
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
