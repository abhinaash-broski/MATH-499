from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome()
driver.get("https://nepsealpha.com/nepse-data")
time.sleep(5)

# get all input fields
inputs = driver.find_elements(By.TAG_NAME, "input")
print("Found inputs:", len(inputs))

# pick likely ones (adjust index if needed)
start_date = inputs[0]
end_date   = inputs[1]

# fill them
start_date.send_keys(Keys.CONTROL, "a")
start_date.send_keys("01/01/2000")
time.sleep(1)

end_date.send_keys(Keys.CONTROL, "a")
end_date.send_keys("09/15/2025")
time.sleep(1)

# click Filter button
filter_btn = driver.find_element(By.XPATH, "//button[contains(., 'Filter')]")
filter_btn.click()
time.sleep(5)
