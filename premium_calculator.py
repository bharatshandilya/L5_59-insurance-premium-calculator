"""Insurance premium calculator with security and quality improvements."""

import http.client
import hmac
import math
import os
import secrets
import ssl
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import urlparse

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

QUOTES = {}
HOST = "127.0.0.1"
UNDERWRITER_TOKEN = os.environ.get("UNDERWRITER_TOKEN", "")
LOG_FILE = os.path.join(tempfile.gettempdir(), "premium_quotes.log")
BASE_RATES = {"health": 5000, "motor": 3000, "life": 8000}


@dataclass(frozen=True)
class PremiumRequest:
    """Hold the inputs required to calculate an insurance premium."""

    policy_type: str
    age: int
    sum_insured: int
    smoker: bool
    claims: int
    discounts: tuple[int, ...] = ()


def calculate_premium(request: PremiumRequest) -> float:
    """Calculate a premium using policy details and applicable discounts."""
    if request.policy_type not in BASE_RATES:
        raise ValueError("Unsupported policy type")

    if request.age < 0 or request.sum_insured < 0 or request.claims < 0:
        raise ValueError(
            "Age, sum insured and claims must be non-negative"
        )

    if not isinstance(request.smoker, bool):
        raise ValueError("smoker must be a Boolean")

    if any(discount < 0 for discount in request.discounts):
        raise ValueError("Discounts must be non-negative")

    premium = (
        BASE_RATES[request.policy_type] + request.sum_insured * 0.002
    )

    if request.age > 45:
        premium *= 1.5

    if request.smoker:
        premium *= 1.3

    premium += request.claims * 1000
    premium -= sum(request.discounts)

    return max(0.0, premium)


def age_from_dob(dob: str) -> int:
    """Calculate age from a date of birth in DD-MM-YYYY format."""
    born = datetime.strptime(dob, "%d-%m-%Y").date()
    today = date.today()

    age = today.year - born.year

    if (today.month, today.day) < (born.month, born.day):
        age -= 1

    if age < 0:
        raise ValueError("Date of birth cannot be in the future")

    return age


def policy_number() -> str:
    """Generate a policy identifier using a secure random generator."""
    return f"POL-{secrets.randbelow(900000) + 100000}"


def save_quote(name: str, premium: float) -> str:
    """Save a quote in memory and append it to the quote log."""
    number = policy_number()
    QUOTES[number] = {"name": name, "premium": premium}

    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"{number},{name},{premium:.2f}\n")

    return number


def import_policies(xml_text: str) -> list[tuple[str, int, int]]:
    """Import valid policy records from XML."""
    try:
        root = ET.fromstring(xml_text)
    except (ET.ParseError, DefusedXmlException):
        return []

    result = []

    for policy in root.findall("policy"):
        try:
            policy_type = policy.get("type")
            age = int(policy.get("age"))
            sum_insured = int(policy.get("sum"))

            if (
                policy_type not in BASE_RATES
                or age < 0
                or sum_insured < 0
            ):
                continue

            result.append((policy_type, age, sum_insured))
        except (TypeError, ValueError):
            continue

    return result


def fetch_rates(url: str) -> bytes:
    """Fetch rate data over a verified HTTPS connection."""
    parsed_url = urlparse(url)

    if parsed_url.scheme != "https" or not parsed_url.hostname:
        raise ValueError("A valid HTTPS URL is required")

    if parsed_url.username or parsed_url.password:
        raise ValueError("Credentials in URLs are not allowed")

    if parsed_url.port not in (None, 443):
        raise ValueError("Only the default HTTPS port is allowed")

    connection = http.client.HTTPSConnection(
        parsed_url.hostname,
        timeout=10,
        context=ssl.create_default_context(),
    )

    try:
        path = parsed_url.path or "/"

        if parsed_url.query:
            path += f"?{parsed_url.query}"

        connection.request("GET", path)
        response = connection.getresponse()

        if response.status != 200:
            raise RuntimeError(
                f"Rate server returned HTTP {response.status}"
            )

        return response.read()
    finally:
        connection.close()


def import_claim_documents(archive_path: str) -> None:
    """Extract claim documents using Python's safe tar filter."""
    destination = "claims_docs"
    os.makedirs(destination, exist_ok=True)

    with tarfile.open(archive_path, "r:*") as archive:
        archive.extractall(destination, filter="data")


def monthly_instalment(premium: float, months: int = 12) -> float:
    """Calculate the monthly instalment for a premium."""
    if months < 0:
        raise ValueError("Months must be non-negative")

    if months == 0:
        return premium

    return math.floor(premium / months)


def is_authorised(token: str) -> bool:
    """Check a token against the configured underwriter token."""
    if not UNDERWRITER_TOKEN:
        return False

    return hmac.compare_digest(token, UNDERWRITER_TOKEN)


def renewal_due(start: str, years: int = 1) -> str:
    """Calculate a renewal date, handling leap-day anniversaries."""
    if years < 0:
        raise ValueError("Years must be non-negative")

    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    target_year = start_date.year + years

    try:
        renewal_date = start_date.replace(year=target_year)
    except ValueError:
        renewal_date = start_date.replace(
            year=target_year, day=28
        )

    return renewal_date.strftime("%Y-%m-%d")


def print_quotes() -> None:
    """Print all saved quotes."""
    print("===== Quote Book =====")

    for index, (number, quote) in enumerate(QUOTES.items(), start=1):
        print(
            index,
            number,
            quote["name"],
            "Rs.",
            quote["premium"],
        )


def main() -> None:
    """Demonstrate premium calculation and supporting functions."""
    first_request = PremiumRequest(
        "health", 30, 500000, False, 0
    )
    second_request = PremiumRequest(
        "health", 30, 500000, False, 0
    )
    motor_request = PremiumRequest(
        "motor", 50, 800000, False, 0
    )
    life_request = PremiumRequest(
        "life", 25, 100000, False, 0, (3000, 3000, 3000)
    )

    first_premium = calculate_premium(first_request)
    second_premium = calculate_premium(second_request)
    motor_premium = calculate_premium(motor_request)
    life_premium = calculate_premium(life_request)

    print("Quote 1:", first_premium)
    print("Quote 2 (same customer details):", second_premium)
    print("Non-smoker aged 50:", motor_premium)
    print("Life with stacked discounts:", life_premium)
    print("Age from DOB 31-12-1990:", age_from_dob("31-12-1990"))
    print("Monthly instalment:", monthly_instalment(motor_premium))
    print("Renewal due:", renewal_due("2025-03-15"))

    sample_xml = (
        "<policies>"
        "<policy type='health' age='40' sum='300000'/>"
        "<policy type='motor' age='abc' sum='1'/>"
        "</policies>"
    )
    print("Imported:", import_policies(sample_xml))
    print("Saved as:", save_quote("Kiran", first_premium))
    print("Authorised:", is_authorised(UNDERWRITER_TOKEN))
    print("Server would listen on", HOST)
    print_quotes()


if __name__ == "__main__":
    main()
