# PriceScraper

PriceScraper is a Python-based web scraping project that reads a CSV file containing SKUs and product URLs, scrapes pricing (and additional information) from various e-commerce websites, and writes the results to output files. The project leverages an object-oriented design and supports multiple websites—including Skroutz, glutenfreeyourself, glutenfreeonline, thanopoulos, and others—using a combination of HTTP requests (with [curl_cffi](https://pypi.org/project/curl-cffi/)), BeautifulSoup, and Selenium.

> **Note:** This project is intended for educational and testing purposes. Always ensure your scraping activities comply with the target websites’ terms of service and local laws.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Multi-Site Scraping:**  
  Scrapes pricing and stock information from various e-commerce sites (e.g., Skroutz, e-fresh, glutenfreeyourself, and more).

- **Object-Oriented Design:**  
  The scraper is encapsulated within a `PriceScraper` class for easier maintainability and extensibility.

- **Hybrid Approach:**  
  Uses a mix of direct HTTP requests (via `curl_cffi` and BeautifulSoup) and browser automation (via Selenium) to handle sites with complex anti-scraping measures.

- **Customizable & Extendable:**  
  Easily add new site-specific scraping logic by extending the provided methods.

---

## Prerequisites

- **Python 3.x**  
- **Firefox Browser:** Required for Selenium automation.
- **Geckodriver:** Ensure it is installed and its path is provided in the configuration.
- **Firefox Profile:** A valid Firefox profile path (used to speed up Selenium by disabling image loading, etc.).
### Python Packages

The project uses the following Python packages:
- `requests`
- `beautifulsoup4`
- `selenium`
- `curl-cffi`
- `fake-useragent`
- (Optional) Additional libraries for proxy rotation or randomization if needed.

   ```bash
   pip install -r requirements.txt

---

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/pricescraper.git
   cd pricescraper
