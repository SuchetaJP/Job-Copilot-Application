"""
services/jd_scraper.py - Scrape job descriptions from URLs

Supports common job posting sites. Falls back to generic
HTML parsing for unknown sites.

NOTE: Some sites actively block scrapers. LinkedIn in particular
requires authentication and has anti-bot measures.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional


# Common job site selectors
# These are CSS selectors that typically contain job description content
SITE_SELECTORS = {
    "linkedin.com": [
        ".description__text",
        ".show-more-less-html__markup",
        "[class*='description']",
    ],
    "indeed.com": [
        "#jobDescriptionText",
        ".jobsearch-jobDescriptionText",
    ],
    "glassdoor.com": [
        ".desc",
        "[class*='JobDescription']",
    ],
    "greenhouse.io": [
        "#content",
        ".content",
    ],
    "lever.co": [
        ".posting-page",
        "[data-qa='job-description']",
    ],
}

# User agent to avoid simple bot blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def scrape_jd_from_url(url: str) -> str:
    """
    Scrape job description text from a URL.
    
    Args:
        url: Full URL to the job posting
    
    Returns:
        Extracted job description text
    
    Raises:
        Exception if scraping fails
    
    LIMITATIONS:
    - Some sites require JavaScript rendering (would need Selenium)
    - LinkedIn often blocks or rate-limits requests
    - Quality varies by site
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove script and style elements
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    
    # Try site-specific selectors first
    for domain, selectors in SITE_SELECTORS.items():
        if domain in url.lower():
            for selector in selectors:
                content = soup.select_one(selector)
                if content:
                    text = content.get_text(separator="\n", strip=True)
                    if len(text) > 100:  # Sanity check
                        return clean_jd_text(text)
    
    # Fallback: try common generic selectors
    generic_selectors = [
        "article",
        ".job-description",
        ".description",
        "[class*='description']",
        "main",
    ]
    
    for selector in generic_selectors:
        content = soup.select_one(selector)
        if content:
            text = content.get_text(separator="\n", strip=True)
            if len(text) > 100:
                return clean_jd_text(text)
    
    # Last resort: get body text
    text = soup.get_text(separator="\n", strip=True)
    if len(text) > 100:
        return clean_jd_text(text[:10000])  # Limit length
    
    raise Exception("Could not extract job description from page")


def clean_jd_text(text: str) -> str:
    """
    Clean up extracted job description text.
    
    - Remove excessive whitespace
    - Remove common boilerplate
    - Normalize line breaks
    """
    # Normalize whitespace
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip very short lines (often navigation artifacts)
        if len(line) < 3:
            continue
        # Skip common boilerplate phrases
        if any(phrase in line.lower() for phrase in [
            "cookie", "privacy policy", "terms of service",
            "sign in", "log in", "create account"
        ]):
            continue
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)
