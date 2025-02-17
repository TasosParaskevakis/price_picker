#!/usr/local/bin/python3
"""
This script reads a CSV file with SKUs and product URLs,
scrapes prices (and extra info) from various e‑commerce sites,
and writes the results to output files.
"""

import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from curl_cffi import requests as curlr
import random
from fake_useragent import UserAgent



class PriceScraper:
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/78.0.3904.108 Safari/537.36'
        )
    }

    def __init__(self, csv_file_path, output_csv, return_file,
                 profile_path, geckodriver_path, headless=True):
        self.csv_file_path = csv_file_path
        self.output_csv = output_csv
        self.return_file = return_file
        self.profile_path = profile_path
        self.geckodriver_path = geckodriver_path
        self.headless = headless
        self.driver = None

    @staticmethod
    def clean_price(price_str):
        """
        Cleans a price string by removing euro symbols, extra spaces, and normalizing
        the decimal separator.
        """
        if not price_str:
            return None
        cleaned = (price_str.replace('€', '')
                             .replace('€/τεμ.', '')
                             .replace(' ', '')
                             .replace('\n', '')
                             .replace('\t', ''))
        cleaned = cleaned.replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def extract_number(text):
        """
        Extracts digits and a single decimal separator (',') from a text.
        """
        number = ''
        decimal_found = False
        for char in text:
            if char.isdigit() or char == ',':
                if char == ',':
                    if not decimal_found:
                        decimal_found = True
                        number += ','
                    else:
                        continue
                else:
                    number += char
            elif char == '.' and not decimal_found:
                number += ','
                decimal_found = True
        return number

    def scrape_via_requests(self, url):
        """
        Returns a BeautifulSoup object for the given URL using the requests library.
        """
        try:
            response = requests.get(url, headers=self.HEADERS)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException:
            return None

    def create_webdriver(self):
        """
        Creates and returns a configured Selenium Firefox WebDriver.
        """
        options = Options()
        options.headless = self.headless

        firefox_profile = webdriver.FirefoxProfile(self.profile_path)
        # Disable images to speed up loading.
        firefox_profile.set_preference("permissions.default.image", 2)

        self.driver = webdriver.Firefox(
            firefox_profile=firefox_profile,
            options=options,
            executable_path=self.geckodriver_path,
            service_log_path='/tmp/geckodriver.log'
        )
        return self.driver

    # ---------------- Site-specific scraping methods (using BeautifulSoup) ----------------

    def scrape_glutenfreeyourself(self, soup):
        try:
            content = soup.find_all('div', class_='basel-scroll-content')
            parsed = BeautifulSoup(str(content), 'html.parser')
            stock = parsed.find('p', class_='stock').get_text(strip=True)
            if stock == 'Εξαντλημένο':
                return '', 'eksantlimeno-glutenfreeyourself.gr', 0, 0
            price_elements = parsed.find_all('span', class_='woocommerce-Price-amount amount')
            price = (price_elements[0].get_text(strip=True)
                     if len(price_elements) == 1
                     else price_elements[1].get_text(strip=True))
            return price, 'glutenfreeyourself.gr', 0, 0
        except Exception:
            return '', 'classnotfound-glutenfreeyourself.gr', 0, 0

    def scrape_glutenfreeonline(self, soup):
        try:
            availability = soup.find(itemprop='availability').get('content')
            if availability == 'http://schema.org/OutOfStock':
                return '', 'eksantlimeno-GlutenFreeOnline.gr', 0, 0
            price = soup.find_all('span', class_='PricesalesPrice')[0].get_text(strip=True)
            return price, 'glutenfreeonline.gr', 0, 0
        except Exception:
            return '', 'classnotfound', 0, 0

    def scrape_thanopoulos(self, soup):
        try:
            price = soup.find('span', id='price_display').get_text(strip=True)
            return price, 'thanopoulos.gr', 0, 0
        except Exception:
            return '', 'classnotfound-thanopoulos.gr', 0, 0

    def scrape_sklavenitis(self, soup):
        try:
            price_text = soup.find('div', class_='price').get_text(strip=True)
            price = self.extract_number(price_text)
            return price, 'sklavenitis.gr', 0, 0
        except Exception:
            return '1000', 'classnotfound-sklavenitis.gr', 0, 0

    def scrape_biohealthyfood(self, soup):
        try:
            content = soup.find_all('div', class_='single-product-content')
            parsed = BeautifulSoup(str(content), 'html.parser')
            stock = parsed.find('p', class_='stock').get_text(strip=True)
            if stock == 'Εξαντλημένο':
                return '', 'eksantlimeno-biohealthyfood.gr', 0, 0
            price_elements = parsed.find_all('span', class_='woocommerce-Price-amount amount')
            price = (price_elements[0].get_text(strip=True)
                     if len(price_elements) == 1
                     else price_elements[1].get_text(strip=True))
            return price, 'biohealthyfood.gr', 0, 0
        except Exception:
            return '', 'classnotfound-biohealthyfood.gr', 0, 0

    def scrape_celiacshop(self, soup):
        try:
            content = soup.find_all('div', class_='product-info summary col-fit col entry-summary product-summary')
            parsed = BeautifulSoup(str(content), 'html.parser')
            price_elements = parsed.find_all('span', class_='woocommerce-Price-amount amount')
            price = (price_elements[0].get_text(strip=True)
                     if len(price_elements) == 1
                     else price_elements[1].get_text(strip=True))
            return price, 'celiacshop.gr', 0, 0
        except Exception:
            return '', 'classnotfound-celiacshop.gr', 0, 0

    def scrape_eblokomarket(self, soup):
        try:
            price = soup.find('span', class_='product-price').get_text(strip=True)
            return price, 'eblokomarket.gr', 0, 0
        except Exception:
            return '', 'classnotfound-eblokomarket.gr', 0, 0

    def scrape_mymarket(self, soup):
        try:
            price = soup.find('span', class_='product-full--final-price').get_text(strip=True)
            return price, 'mymarket.gr', 0, 0
        except Exception:
            return '', 'classnotfound-mymarket.gr', 0, 0

    def scrape_bio2go(self, soup):
        try:
            price = soup.find('span', id='price').get_text(strip=True)
            return price, 'bio2go.gr', 0, 0
        except Exception:
            return '', 'classnotfound-bio2go.gr', 0, 0

    def scrape_wefit(self, soup):
        try:
            price = soup.find('span', class_='actual-price').get_text(strip=True)
            return price, 'wefit.gr', 0, 0
        except Exception:
            return '', 'classnotfound-wefit.gr', 0, 0

    def scrape_2pharmacy(self, soup):
        try:
            price = soup.find('span', id='our_price_display').get_text(strip=True)
            return price, '2pharmacy.gr', 0, 0
        except Exception:
            return '', 'classnotfound-2pharmacy.gr', 0, 0

    def scrape_greenhousebio(self, soup):
        try:
            price = soup.find('span', itemprop='price').get_text(strip=True)
            return price, 'greenhousebio.gr', 0, 0
        except Exception:
            return '', 'classnotfound-greenhousebio.gr', 0, 0

    # ---------------- Site-specific scraping methods (using Selenium / API) ----------------

    def scrape_skroutz(self, url):
        our_shop_id = 12345
        attempts = 0
        try:
            product_id = url.split("/s/")[1].split("/")[0]
        except IndexError:
            print("Invalid skroutz URL format")
            return '', 'Invalid URL', 0, 0

        api_url = f"https://www.skroutz.gr/s/{product_id}/filter_products.json"

        # Define your enhanced headers
        ua = UserAgent()
        random_ua = ua.random


        custom_headers = {
            'User-Agent': random_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': url,  # use the actual product URL as referer
            'Connection': 'keep-alive',
            'VIEWPORT-WIDTH': '1920',
            'Cookie': '*'
        }

        while attempts < 3:
            try:
                response = curlr.get(api_url, impersonate="chrome", headers=custom_headers)
                if response.status_code == 403:
                    print("403 Forbidden received, trying again after delay...")
                    time.sleep(5)
                    attempts += 1
                    continue
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", 5)
                    print(f"Rate limited. Waiting for {retry_after} seconds...")
                    time.sleep(int(retry_after))
                    attempts += 1
                    continue
                elif response.status_code != 200:
                    print(f"Unexpected status code: {response.status_code}")
                    attempts += 1
                    continue

                data = response.json()
                shop_count = data.get("shop_count", 0)
                product_cards = data.get("product_cards", {})

                prices = []
                shops = []
                for card in product_cards.values():
                    shop_id = card.get("shop_id")
                    raw_price = card.get("raw_price", 0.0)
                    prices.append((raw_price, shop_id))
                    products = card.get("products", [{}])
                    shop_name = products[0].get("name", "") if isinstance(products, list) and products else ""
                    shops.append(shop_name)

                prices.sort(key=lambda x: x[0])

                if prices and prices[0][1] == our_shop_id:
                    if len(prices) > 1:
                        competitor_price = prices[1][0]
                        price_value = competitor_price
                        skroutzprice = competitor_price
                    else:
                        price_value = None
                        skroutzprice = None
                else:
                    if prices:
                        price_value = prices[0][0]
                        skroutzprice = prices[0][0]
                    else:
                        price_value = None
                        skroutzprice = None

                site = "skroutz"
                return (str(price_value) if price_value is not None else '',
                        site,
                        shop_count,
                        str(skroutzprice) if skroutzprice is not None else '')
            except curlr.RequestsError as e:
                print(f"Error: {e}")
                attempts += 1
                time.sleep(5)
            except Exception as e:
                print(f"Unexpected error: {e}")
                attempts += 1
                time.sleep(5)

        return '', 'classnotfound-skroutz.gr', 0, 0

    def scrape_efresh(self, url):
        """
        Scrapes the e-fresh.gr page using Selenium.
        """
        try:
            self.driver.get(url)
            self.driver.execute_script('window.scrollTo(0, 0)')
            is_404 = False
            try:
                self.driver.find_element_by_class_name('error-404')
                is_404 = True
            except Exception:
                is_404 = False

            if not is_404:
                price_elements = self.driver.find_elements_by_class_name('price')
                if len(price_elements) > 1:
                    price_text = price_elements[1].text
                elif price_elements:
                    price_text = price_elements[0].text
                else:
                    price_text = ''
                lines = price_text.split('\n')
                price = lines[1] if len(lines) > 1 else lines[0]
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                return price, 'e-fresh.gr', 0, 0
            else:
                return '', 'classnotfound-e-fresh.gr', 0, 0
        except Exception:
            return '', 'classnotfound-e-fresh.gr', 0, 0

    # ---------------- Dispatcher ----------------

    def search(self, url):
        """
        Determines the proper scraping method for the given URL.
        Returns a tuple: (price_str, site_name, store_count, skroutz_price_cleaned)
        """
        if 'skroutz' in url or 'e-fresh' in url:
            self.driver.delete_all_cookies()

        if 'skroutz.gr' in url:
            return self.scrape_skroutz(url)
        if 'e-fresh.gr' in url:
            return self.scrape_efresh(url)

        soup = self.scrape_via_requests(url)
        if soup is None:
            return '', 'Error', 0, 0

        if 'glutenfreeyourself.gr' in url:
            return self.scrape_glutenfreeyourself(soup)
        elif 'glutenfreeonline.gr' in url:
            return self.scrape_glutenfreeonline(soup)
        elif 'thanopoulos.gr' in url:
            return self.scrape_thanopoulos(soup)
        elif 'sklavenitis.gr' in url:
            return self.scrape_sklavenitis(soup)
        elif 'biohealthyfood.gr' in url:
            return self.scrape_biohealthyfood(soup)
        elif 'celiacshop.gr' in url:
            return self.scrape_celiacshop(soup)
        elif 'eblokomarket.gr' in url:
            return self.scrape_eblokomarket(soup)
        elif 'mymarket.gr' in url:
            return self.scrape_mymarket(soup)
        elif 'bio2go.gr' in url:
            return self.scrape_bio2go(soup)
        elif 'wefit.gr' in url:
            return self.scrape_wefit(soup)
        elif '2pharmacy.gr' in url:
            return self.scrape_2pharmacy(soup)
        elif 'greenhousebio.gr' in url:
            return self.scrape_greenhousebio(soup)
        else:
            return '', 'site-NA', 0, 0

    # ---------------- CSV Processing ----------------

    def process_csv(self):
        results = []
        self.create_webdriver()
        url_counter = 0

        with open(self.csv_file_path, mode='r', encoding='utf-16') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                sku = row[0]
                urls = row[1].split("    ")
                prices = []
                site_names = []
                store_counts = []
                skroutz_prices = []

                for url in urls:
                    if 'http' not in url:
                        continue

                    if 'skroutz' in url:
                        url_counter += 1
                        if url_counter % 10 == 0:
                            self.driver.quit()
                            self.create_webdriver()

                    price_str, site_name, store_count, skroutz_price = self.search(url)

                    if price_str:
                        price_value = self.clean_price(price_str)
                        if price_value is not None:
                            prices.append(price_value)
                    skroutz_value = self.clean_price(skroutz_price)
                    skroutz_prices.append(skroutz_value if skroutz_value is not None else 0)
                    site_names.append(site_name)
                    store_counts.append(int(store_count) if isinstance(store_count, int) else 0)

                if prices:
                    min_price = min(prices)
                    index = prices.index(min_price)
                    final_site = site_names[index]
                    max_store_count = max(store_counts) if max(store_counts) > 0 else ""
                    max_skroutz_price = max(skroutz_prices) if max(skroutz_prices) > 0 else ""
                    results.append((sku, final_site, min_price, max_store_count, max_skroutz_price))

                    with open(self.return_file, mode='a') as ret_file:
                        ret_file.write(f"{sku}, {min_price}, {final_site}, {store_counts}, {skroutz_prices}\n")

        self.driver.quit()

        with open(self.output_csv, mode='w', newline='') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(['SKU', 'Site', 'Price', 'Store_Count', 'Skroutz_Price'])
            writer.writerows(results)


# ---------------- Main Execution ----------------

if __name__ == '__main__':

    csv_file_path_test = '/Users/user/Desktop/urls.csv'
    csv_file_path_server = '/Library/FileMaker Server/Data/Scripts/urls.csv'
    csv_file_path= csv_file_path_test

    output_csv_test = '/Users/user/Desktop/price-new1.csv'
    output_csv_server = '/Library/FileMaker Server/Data/Scripts/prices.csv'
    output_csv = output_csv_test

    return_file_test = '/Users/user/Desktop/return1.txt'
    return_file_server = '/Library/FileMaker Server/Data/Scripts/return.txt'
    return_file = return_file_test

    profile_path_test = '/Users/user/Library/Application Support/Firefox/Profiles/2ek7i7id.default-1568037803549'
    profile_path_server = '/Users/admin/Library/Application Support/Firefox/Profiles/e1lsnk4m.default-release'
    profile_path = profile_path_test
    geckodriver_path = '/Library/Frameworks/Python.framework/geckodriver'

    scraper = PriceScraper(csv_file_path, output_csv, return_file,
                           profile_path, geckodriver_path, headless=True)
    scraper.process_csv()
