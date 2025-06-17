# countrymap.py - Mapping of countries to their flag codes (Vercel-style)

FLAG_MAP = {
    # Major Countries
    "United States": "US",
    "United Kingdom": "GB",
    "Canada": "CA",
    "Australia": "AU",
    "Germany": "DE",
    "France": "FR",
    "Italy": "IT",
    "Spain": "ES",
    "Netherlands": "NL",
    "Japan": "JP",
    "South Korea": "KR",
    "China": "CN",
    "India": "IN",
    "Brazil": "BR",
    "Mexico": "MX",
    "Russia": "RU",
    # European Countries
    "Austria": "AT",
    "Belgium": "BE",
    "Switzerland": "CH",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Finland": "FI",
    "Greece": "GR",
    "Hungary": "HU",
    "Ireland": "IE",
    "Luxembourg": "LU",
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Sweden": "SE",
    "Turkey": "TR",
    "Ukraine": "UA",
    "Romania": "RO",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Slovenia": "SI",
    "Slovakia": "SK",
    "Estonia": "EE",
    "Latvia": "LV",
    "Lithuania": "LT",
    # Asian Countries
    "Singapore": "SG",
    "Malaysia": "MY",
    "Thailand": "TH",
    "Indonesia": "ID",
    "Philippines": "PH",
    "Vietnam": "VN",
    "Taiwan": "TW",
    "Hong Kong": "HK",
    "Bangladesh": "BD",
    "Pakistan": "PK",
    "Sri Lanka": "LK",
    "Nepal": "NP",
    "Myanmar": "MM",
    "Cambodia": "KH",
    "Laos": "LA",
    # Middle East & Africa
    "Israel": "IL",
    "Saudi Arabia": "SA",
    "United Arab Emirates": "AE",
    "Qatar": "QA",
    "Kuwait": "KW",
    "Bahrain": "BH",
    "Oman": "OM",
    "Jordan": "JO",
    "Lebanon": "LB",
    "Egypt": "EG",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Kenya": "KE",
    "Morocco": "MA",
    "Tunisia": "TN",
    "Ghana": "GH",
    "Ethiopia": "ET",
    # Americas
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Venezuela": "VE",
    "Uruguay": "UY",
    "Ecuador": "EC",
    "Bolivia": "BO",
    "Paraguay": "PY",
    "Costa Rica": "CR",
    "Panama": "PA",
    "Guatemala": "GT",
    "Honduras": "HN",
    "El Salvador": "SV",
    "Nicaragua": "NI",
    "Dominican Republic": "DO",
    "Jamaica": "JM",
    "Cuba": "CU",
    "Puerto Rico": "PR",
    # Oceania
    "New Zealand": "NZ",
    "Fiji": "FJ",
    "Papua New Guinea": "PG",
    # Common variations and alternative names
    "USA": "US",
    "US": "US",
    "America": "US",
    "UK": "GB",
    "Britain": "GB",
    "England": "GB",
    "UAE": "AE",
    "South Korea": "KR",
    "North Korea": "KP",
    # Default for unknown/others
    "Unknown": "UNKNOWN",
    "Others": "UNKNOWN",
    "N/A": "UNKNOWN",
    "": "UNKNOWN",
}


def get_flag_code(country_name: str) -> str:
    """
    Get flag code for a country name (Vercel-style).
    Returns 'UNKNOWN' if country not found.

    Args:
        country_name: Name of the country

    Returns:
        Two-letter country code or 'UNKNOWN'
    """
    if not country_name:
        return "UNKNOWN"

    # Try exact match first
    if country_name in FLAG_MAP:
        return FLAG_MAP[country_name]

    # Try case-insensitive match
    country_lower = country_name.lower()
    for country, code in FLAG_MAP.items():
        if country.lower() == country_lower:
            return code

    # Default fallback
    return "UNKNOWN"
