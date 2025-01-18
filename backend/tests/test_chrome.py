from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome_setup():
    print("Setting up Chrome options...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    print("Initializing Chrome driver...")
    driver = webdriver.Chrome(options=chrome_options)
    
    print("Testing with a simple page load...")
    driver.get("https://www.google.com")
    print(f"Page title: {driver.title}")
    
    print("Closing driver...")
    driver.quit()
    
    print("Test completed successfully!")

if __name__ == "__main__":
    try:
        test_chrome_setup()
    except Exception as e:
        print(f"Test failed with error: {str(e)}")