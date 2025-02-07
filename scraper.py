from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from dotenv import load_dotenv
import os


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
def scrape_jobs():
    """Scrapes job data from the SimplifyJobs New-Grad-Positions repository."""
    logging.info("Starting scrape_jobs function")
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        url = os.getenv('REMOTE_SCRAPE')
        driver.get(url)
        logging.info(f"Navigated to {url}")

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "markdown-accessiblity-table"))
            )
            logging.info("Table loaded successfully")
        except TimeoutException:
            logging.warning("Timeout waiting for table to load.")
            return []

        jobs = []

        #Find the parent 
        table_parent = driver.find_element(By.XPATH,"//article[@itemprop='text']")
        rows = table_parent.find_elements(By.TAG_NAME, "tr")
        logging.info(f"Found {len(rows)} rows in the table")

        for row in rows[1:]: 
                if len(jobs) >= 10:
                    break
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 5:
                     try:
                         company = cells[0].find_element(By.TAG_NAME,"strong").text.strip()
                         position = cells[1].text.strip()
                         location = cells[2].text.strip()
                         application_link = cells[3].find_element(By.TAG_NAME, "a").get_attribute("href") if cells[3].find_elements(By.TAG_NAME, "a") else "Link Not Available"

                         # Check for filled position
                         if application_link == "Link Not Available":
                            status = "Position Filled"
                         else:
                            status = "Open"


                         date_posted = cells[4].text.strip()

                         jobs.append({
                            "company": company,
                            "position": position,
                            "location": location,
                            "application_link": application_link,
                            "date_posted": date_posted,
                            "status": status, #added
                        })
                         logging.info(f"Extracted job: {company} - {position}")

                     except NoSuchElementException as e:
                         logging.warning(f"Error extracting data from row: {e}")
                else:
                   logging.warning(f"Row has fewer than 5 cells, skipping")

        logging.info(f"Successfully scraped {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}", exc_info=True)
        return []

    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed")
        logging.info("Exiting scrape_jobs function")


if __name__ == '__main__':
    jobs = scrape_jobs()
    if jobs:
        for job in jobs:
            print(job)
    else:
        print("No jobs found or an error occurred.")