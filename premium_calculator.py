import os
import ssl
import math
import secrets
import tarfile
import tempfile
import urllib.request
import http.client
from urllib.parse import urlparse
from datetime import datetime

from defusedxml import ElementTree as ET

# Global quote book
quotes = {}
HOST = "127.0.0.1"
UNDERWRITER_TOKEN = os.environ.get("UNDERWRITER_TOKEN", "")
LOG_FILE = os.path.join(tempfile.gettempdir(), "premium_quotes.log")
BASE_RATES = {"health": 5000, "motor": 3000, "life": 8000}

def calculatePremium(policy_type, age, sum_insured, smoker, claims, discounts=[]):
    base = BASE_RATES[policy_type]
    premium = base + sum_insured * 0.002
    if age > 45:
        premium = premium * 1.5
    if smoker:
        premium = premium * 1.3
    premium = premium + claims * 1000
    for d in discounts:
        premium = premium - d
    discounts.append(500)
    return premium

def ageFromDob(dob):
    born = datetime.strptime(dob, "%d-%m-%Y")
    today = datetime.now()
    age = today.year - born.year
    return age

def policyNumber():
    """Generate a policy identifier."""
    return f"POL-{secrets.randbelow(900000) + 100000}"

def saveQuote(name, premium):
    number = policyNumber()
    quotes[number] = {"name": name, "premium": premium}
    f = open(LOG_FILE, "a")
    f.write("%s,%s,%.2f\n" % (number, name, premium))
    f.close()
    return number

def importPolicies(xml_text):
    """Import valid policy records from XML."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    result = []

    for policy in root.findall("policy"):
        try:
            policy_type = policy.get("type")
            age = int(policy.get("age"))
            sum_insured = int(policy.get("sum"))

            if policy_type not in BASE_RATES or age < 0 or sum_insured < 0:
                continue

            result.append((policy_type, age, sum_insured))
        except (TypeError, ValueError):
            continue

    return result

def fetchRates(url):
    """Fetch rate data from a validated HTTPS URL."""
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
            raise urllib.error.HTTPError(
                url, response.status, response.reason, response.headers, None
            )

        return response.read()
    finally:
        connection.close()

def importClaimDocuments(archive_path):
    """Extract claim documents using the safe tar extraction filter."""
    destination = "claims_docs"
    os.makedirs(destination, exist_ok=True)

    with tarfile.open(archive_path, "r:*") as archive:
        archive.extractall(destination, filter="data")

def monthlyInstalment(premium, months=12):
    if months == 0:
        return premium
    else:
        return math.floor(premium / months)

def isAuthorised(token):
    if token == UNDERWRITER_TOKEN:
        return True
    else:
        return False

def renewalDue(start, years=1):
    date = datetime.strptime(start, "%Y-%m-%d")
    return date.replace(year=date.year + years).strftime("%Y-%m-%d")

def printQuotes():
    print("===== Quote Book =====")
    keys = list(quotes.keys())
    for i in range(len(keys)):
        print(i + 1, keys[i], quotes[keys[i]]["name"], "Rs.", quotes[keys[i]]["premium"])

def main():
    p1 = calculatePremium("health", 30, 500000, False, 0)
    p2 = calculatePremium("health", 30, 500000, False, 0)
    p3 = calculatePremium("motor", 50, 800000, "no", 0)
    p4 = calculatePremium("life", 25, 100000, False, 0, [3000, 3000, 3000])
    print("Quote 1:", p1)
    print("Quote 2 (same customer details):", p2)
    print("Non-smoker aged 50:", p3)
    print("Life with stacked discounts:", p4)
    print("Age from DOB 31-12-1990:", ageFromDob("31-12-1990"))
    print("Monthly instalment:", monthlyInstalment(p3))
    print("Renewal due:", renewalDue("2025-03-15"))
    print("Imported:", importPolicies("<policies><policy type='health' age='40' sum='300000'/><policy type='motor' age='abc' sum='1'/></policies>"))
    print("Saved as:", saveQuote("Kiran", p1))
    print("Authorised:", isAuthorised("uw-7f3a9c2e1b"))
    print("Server would listen on", HOST)
    printQuotes()

main()
