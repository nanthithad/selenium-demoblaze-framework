# utilities/utility_methods.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import *
from PIL import Image
import time
import os
import random
import string
import threading
from datetime import datetime
from faker import Faker
import io  # Required for BytesIO in full-page screenshot

# Thread-safe screenshot counter
screenshot_lock = threading.Lock()
screenshot_counter = {}


class UtilityMethods:
    def __init__(self, driver, logger):
        """Initialize UtilityMethods with WebDriver and logger."""
        self.driver = driver
        self.logger = logger
        self.faker = Faker()

    def _get_thread_safe_filename(self, base_name):
        """Generate a thread-safe unique filename."""
        with screenshot_lock:
            thread_id = threading.current_thread().ident
            if thread_id not in screenshot_counter:
                screenshot_counter[thread_id] = 0
            screenshot_counter[thread_id] += 1
            counter = screenshot_counter[thread_id]

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')

        return f"{base_name}_{worker_id}_{timestamp}_{counter}"

    def take_screenshot(self, name=None):
        """Take screenshot with thread-safe timestamp."""
        try:
            if not name:
                name = "screenshot"

            # Create screenshots directory in reports folder
            screenshot_dir = os.path.join(os.getcwd(), 'reports', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

            # Generate thread-safe filename
            filename = self._get_thread_safe_filename(name)
            filepath = os.path.join(screenshot_dir, f"{filename}.png")

            self.driver.save_screenshot(filepath)
            self.logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            return None

    def take_element_screenshot(self, element, name=None):
        """Take screenshot of specific element with thread-safe naming."""
        try:
            if not name:
                name = "element"

            screenshot_dir = os.path.join(os.getcwd(), 'reports', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

            # Generate thread-safe filename
            filename = self._get_thread_safe_filename(name)
            filepath = os.path.join(screenshot_dir, f"{filename}.png")

            element.screenshot(filepath)
            self.logger.info(f"Element screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to take element screenshot: {str(e)}")
            return None

    def take_full_page_screenshot(self, name=None):
        """Take full page screenshot by scrolling and stitching."""
        try:
            if not name:
                name = "fullpage"

            # Get full page dimensions
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            total_width = self.driver.execute_script("return document.body.scrollWidth")

            # Create a blank image to stitch screenshots
            stitched_image = Image.new('RGB', (total_width, total_height))

            scroll_position = 0
            while scroll_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                time.sleep(0.5)  # Allow time for lazy content to load

                # Capture screenshot of current viewport
                screenshot_png = self.driver.get_screenshot_as_png()
                screenshot_image = Image.open(io.BytesIO(screenshot_png))

                # Paste into the full image at correct vertical offset
                stitched_image.paste(screenshot_image, (0, scroll_position))

                scroll_position += viewport_height

            # Save stitched image with thread-safe naming
            screenshot_dir = os.path.join(os.getcwd(), 'reports', 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)

            filename = self._get_thread_safe_filename(name)
            filepath = os.path.join(screenshot_dir, f"{filename}.png")

            stitched_image.save(filepath)
            self.logger.info(f"Full page screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to take full page screenshot: {str(e)}")
            return None

    def scroll_to_element(self, element):
        """Scroll to make element visible."""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)

    def scroll_by_pixels(self, x_pixels, y_pixels):
        """Scroll by specific pixels."""
        self.driver.execute_script(f"window.scrollBy({x_pixels}, {y_pixels});")

    def scroll_to_bottom(self):
        """Scroll to bottom of page."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_to_top(self):
        """Scroll to top of page."""
        self.driver.execute_script("window.scrollTo(0, 0);")

    def highlight_element(self, element, duration=2):
        """Highlight element with a red border and yellow background."""
        try:
            original_style = element.get_attribute('style') or ''
            self.driver.execute_script(
                "arguments[0].setAttribute('style', arguments[1]);",
                element,
                "border: 3px solid red; background: yellow;"
            )
            time.sleep(duration)
            self.driver.execute_script(
                "arguments[0].setAttribute('style', arguments[1]);",
                element,
                original_style
            )
        except Exception as e:
            self.logger.error(f"Failed to highlight element: {str(e)}")

    def execute_javascript(self, script, *args):
        """Execute synchronous JavaScript code."""
        return self.driver.execute_script(script, *args)

    def execute_async_javascript(self, script, *args):
        """Execute asynchronous JavaScript code."""
        return self.driver.execute_async_script(script, *args)

    def generate_random_string(self, length=10, chars=None):
        """Generate a random string of given length and character set."""
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    def generate_random_email(self):
        """Generate a random email using Faker."""
        return self.faker.email()

    def generate_random_phone(self):
        """Generate a random phone number using Faker."""
        return self.faker.phone_number()

    def generate_random_name(self):
        """Generate a random full name using Faker."""
        return self.faker.name()

    def generate_random_address(self):
        """Generate a random address using Faker."""
        return self.faker.address()

    def generate_random_number(self, min_val=1, max_val=100):
        """Generate random number."""
        return random.randint(min_val, max_val)

    def wait_for_ajax_complete(self, timeout=30):
        """Wait for jQuery AJAX calls to complete (requires jQuery on page)."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return typeof jQuery !== 'undefined' && jQuery.active == 0")
            )
        except JavascriptException:
            self.logger.warning("jQuery not found on page. Skipping AJAX wait.")

    def wait_for_angular_load(self, timeout=30):
        """Wait for Angular application to stabilize."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script(
                    "return window.getAllAngularTestabilities().findIndex(x=>!x.isStable()) === -1"
                )
            )
        except JavascriptException:
            self.logger.warning("Angular not detected. Skipping Angular wait.")

    def wait_for_element(self, locator, timeout=10):
        """Wait for element to be present."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {locator}")
            return None

    def wait_for_element_clickable(self, locator, timeout=10):
        """Wait for element to be clickable."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable(locator))
            return element
        except TimeoutException:
            self.logger.error(f"Element not clickable: {locator}")
            return None

    def wait_for_element_visible(self, locator, timeout=10):
        """Wait for element to be visible."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located(locator))
            return element
        except TimeoutException:
            self.logger.error(f"Element not visible: {locator}")
            return None

    def get_browser_logs(self, log_type='browser'):
        """Get browser console logs (e.g., 'browser', 'driver', 'client', 'server')."""
        try:
            return self.driver.get_log(log_type)
        except Exception as e:
            self.logger.error(f"Failed to retrieve {log_type} logs: {e}")
            return []

    def get_performance_metrics(self):
        """Get page performance timing metrics."""
        try:
            return self.driver.execute_script(
                "return window.performance.getEntriesByType('navigation')[0];"
            )
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {}

    def get_network_conditions(self):
        """Get current network conditions (Chrome DevTools Protocol)."""
        try:
            return self.driver.execute_cdp_cmd('Network.getConditions', {})
        except Exception as e:
            self.logger.error(f"Failed to get network conditions: {e}")
            return {}

    def set_network_conditions(self, offline=False, latency=0,
                               download_throughput=-1, upload_throughput=-1):
        """Set network conditions using CDP (Chrome only)."""
        try:
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': offline,
                'latency': latency,
                'downloadThroughput': download_throughput,
                'uploadThroughput': upload_throughput
            })
            self.logger.info(f"Network conditions set: offline={offline}, latency={latency}ms")
        except Exception as e:
            self.logger.error(f"Failed to set network conditions: {e}")

    def get_local_storage(self):
        """Get all items from localStorage as a dict."""
        try:
            return self.driver.execute_script(
                "return Object.keys(localStorage).reduce((obj, key) => { obj[key] = localStorage.getItem(key); return obj; }, {});"
            )
        except Exception as e:
            self.logger.error(f"Failed to get local storage: {e}")
            return {}

    def set_local_storage(self, key, value):
        """Set a key-value pair in localStorage."""
        try:
            self.driver.execute_script(f"localStorage.setItem(arguments[0], arguments[1]);", key, value)
        except Exception as e:
            self.logger.error(f"Failed to set local storage: {e}")

    def clear_local_storage(self):
        """Clear all localStorage data."""
        try:
            self.driver.execute_script("localStorage.clear();")
        except Exception as e:
            self.logger.error(f"Failed to clear local storage: {e}")

    def get_session_storage(self):
        """Get all items from sessionStorage as a dict."""
        try:
            return self.driver.execute_script(
                "return Object.keys(sessionStorage).reduce((obj, key) => { obj[key] = sessionStorage.getItem(key); return obj; }, {});"
            )
        except Exception as e:
            self.logger.error(f"Failed to get session storage: {e}")
            return {}

    def set_session_storage(self, key, value):
        """Set a key-value pair in sessionStorage."""
        try:
            self.driver.execute_script(f"sessionStorage.setItem(arguments[0], arguments[1]);", key, value)
        except Exception as e:
            self.logger.error(f"Failed to set session storage: {e}")

    def clear_session_storage(self):
        """Clear all sessionStorage data."""
        try:
            self.driver.execute_script("sessionStorage.clear();")
        except Exception as e:
            self.logger.error(f"Failed to clear session storage: {e}")

    def check_broken_links(self, check_external_only=False):
        """
        Check for broken links on the current page.
        Returns a dict with counts and list of broken links.
        Thread-safe implementation for parallel execution.
        """
        from urllib.parse import urljoin, urlparse
        import requests
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.logger.info("Checking for broken links...")
        links = self.driver.find_elements(By.TAG_NAME, "a")
        self.logger.info(f"Found {len(links)} links")

        broken_links = []
        valid_links = []
        base_url = self.driver.current_url

        for link in links:
            href = link.get_attribute("href")
            if not href or href.startswith(("javascript:", "#", "mailto:", "tel:")):
                continue
            # Skip relative URLs (they cause SSL errors when treated as absolute)
            if href.startswith("/") or "://" not in href:
                self.logger.debug(f"Skipping relative/internal link: {href}")
                continue

            # Skip external links if flag is set
            if check_external_only:
                if urlparse(href).netloc == urlparse(base_url).netloc:
                    continue

            try:
                # Use HEAD request for efficiency
                response = requests.head(href, timeout=5, allow_redirects=True, verify=False)
                # Fallback to GET if HEAD not allowed
                if response.status_code >= 400 or response.status_code == 405:
                    response = requests.get(href, timeout=5, verify=False)
                if response.status_code >= 400:
                    broken_links.append((href, response.status_code))
                    self.logger.warning(f"BROKEN LINK: {href} | Status: {response.status_code}")
                else:
                    valid_links.append(href)
            except Exception as e:
                broken_links.append((href, f"Error: {str(e)}"))
                self.logger.error(f"LINK ERROR: {href} | Exception: {e}")

        summary = {
            "total_links_checked": len(valid_links) + len(broken_links),
            "valid_links": len(valid_links),
            "broken_links": len(broken_links),
            "broken_list": broken_links
        }

        self.logger.info(
            f"Success: Broken Links Check Complete: {summary['broken_links']} broken out of {summary['total_links_checked']}")
        return summary