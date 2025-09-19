import os
import time
import sys
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


# --------------------
# Selenium Setup
# --------------------
def get_driver():
    options = Options()
    options.headless = True
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(120)
    return driver


# --------------------
# Search by Date
# --------------------
def search(driver, date):
    driver.get("https://www.sharesansar.com/today-share-price")

    # Locate date input
    date_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-date-format='YYYY-MM-DD']"))
    )

    # Clear and enter new date
    driver.execute_script("arguments[0].value = '';", date_input)
    date_input.send_keys(date)

    time.sleep(1)  # let calendar close

    # Click search button via JS
    search_btn = driver.find_element(By.ID, "btn_todayshareprice_submit")
    driver.execute_script("arguments[0].click();", search_btn)

    # Check if no data message appears
    if driver.find_elements(By.XPATH, "//*[contains(text(), 'Could not find floorsheet matching the search criteria')]"):
        print(f"❌ No data found for {date}")
        return False
    return True


# --------------------
# Extract Table
# --------------------
def get_page_table(driver):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "headFixed"))
    )
    soup = BeautifulSoup(driver.page_source, "lxml")
    table = soup.find("table", {"id": "headFixed"})
    tab_data = [[cell.text.strip() for cell in row.find_all(["th", "td"])]
                for row in table.find_all("tr")]
    df = pd.DataFrame(tab_data)
    return df


# --------------------
# Scrape Data for One Date
# --------------------
def scrape_data(driver, date):
    if not search(driver, date):
        return pd.DataFrame()

    df = pd.DataFrame()
    count = 0
    while True:
        count += 1
        print(f"   ↳ Scraping page {count}")
        page_table_df = get_page_table(driver)
        df = pd.concat([df, page_table_df], ignore_index=True)
        try:
            next_btn = driver.find_element(By.LINK_TEXT, "Next")
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
        except NoSuchElementException:
            break
    return df


# --------------------
# Clean DataFrame
# --------------------
def clean_df(df):
    if df.empty:
        return df
    new_df = df.drop_duplicates(keep="first")
    new_header = new_df.iloc[0]  # first row is header
    new_df = new_df[1:]          # the rest is data
    new_df.columns = new_header
    if "S.No" in new_df.columns:
        new_df.drop(["S.No"], axis=1, inplace=True)
    return new_df


# --------------------
# Main Loop
# --------------------
def main():
    os.makedirs("data", exist_ok=True)
    driver = get_driver()

    start_date = datetime(2000, 1, 1)
    end_date = datetime.today()

    current_date = start_date
    while current_date <= end_date:
        # Skip weekends (Nepal Stock Exchange is closed)
        if current_date.weekday() >= 4:  # 5=Saturday, 6=Sunday
            current_date += timedelta(days=1)
            continue

        date_str = current_date.strftime("%Y-%m-%d")
        file_name = date_str.replace("-", "_")
        file_path = f"data/{file_name}.csv"

        if os.path.exists(file_path):
            print(f"⚡ Skipping {date_str}, already scraped.")
        else:
            print(f"📅 Scraping {date_str} ...")
            df = scrape_data(driver, date_str)
            final_df = clean_df(df)
            if not final_df.empty:
                final_df.to_csv(file_path, index=False)
                print(f"✅ Saved {file_path}")
            else:
                print(f"⚠️ No data for {date_str}")

        current_date += timedelta(days=1)

    driver.quit()


if __name__ == "__main__":
    main()
