import os
import json
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
from google_play_scraper import app, search
from google_play_scraper.exceptions import NotFoundError
from urllib3.exceptions import IncompleteRead
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException



# Function to fetch launcher icon URL for an app

def get_icon_url(package_name):
    try:
        result = app(package_name)
        return result.get('icon')
    except NotFoundError:
        return None  # Return None if app not found
        
    
def get_first_screenshot_url(package_name):
    try:
        result = app(package_name)
        screenshots = result.get('screenshots')
        if screenshots:
            return screenshots[0]  # Return the URL of the first screenshot
        else:
            return None
    except NotFoundError:
        return None  # Return None if app not found
    

def get_app_img_apkpure(app_name): # XXX: this function needs refactoring/cleaning.
    print(" getting icon link for %s" %(app_name))
    url = "https://apkpure.com/search?q=%s" %(app_name)
    #html = requests.get(url)
    options = webdriver.EdgeOptions()
    options.add_argument("--enable-chrome-browser-cloud-management")
    driver = webdriver.Edge(options=options)
    driver.get(url)
    #assert "Python" in driver.title
    #elem = driver.find_element(By.CLASS_NAME, "first-info")
    #text = driver.find_element(By.CSS_SELECTOR('.first-info a').get_attribute('href'))
    #assert  in driver.title
    try:
        button = driver.find_element(By.CLASS_NAME, "first-info")
        button.click()
    except NoSuchElementException:
        print("package "+ app_name + " not found in apkpure")
        driver.close()
        return None
    try:
        pagecheck = driver.find_element(By.CLASS_NAME, "download_apk_news")
        packagename = pagecheck.get_attribute("data-dt-package_name")
        if (app_name == packagename):
            print("page check complete")
        else:
            print("package " + app_name + " not found in apkpure")
            driver.close()
            return None
    except NoSuchElementException:
        print("package name check failed")
    
    icon_div = driver.find_element(By.CLASS_NAME, "apk_info")
    icon = icon_div.find_element(By.TAG_NAME,"img")
    iconsrc=icon.get_attribute("src")
    try:
        scrnshot_div = driver.find_element(By.CLASS_NAME, "b")
        scrnshot = scrnshot_div.find_element(By.TAG_NAME,"a")
        scrnshotsrc = scrnshot.get_attribute("href")
    except NoSuchElementException:
        print("package " + app_name + " doesn't have screenshots")
        driver.close()
        return(iconsrc,None)
    driver.close()
    #soup = BeautifulSoup(html.content, "lxml")
    #print(soup)
    #for i in soup.findAll("a", class_="first-info"):
    #    print(i)
    #    a_url = i["href"]
        #html2 = requests.get(a_url)

        #parse2 = BeautifulSoup(html2.text)
        #for link in parse2.find_all("a",id="download_link"):
        #    download_link = link["href"]
    return (iconsrc,scrnshotsrc)



# Function to search for the app title and return the package name
def get_package_name(app_title):
    try:
        # Encode the app title using UTF-8 encoding
        app_title_encoded = app_title.encode('utf-8')
        
        # Search for the encoded app title
        results = search(app_title_encoded, n_hits=1)  # Search for the app title, limit to 1 result
        if results:
            return results[0]['appId']  # Return the package name (appId) of the first result
    except Exception as e:
        print(f"Error occurred while searching for {app_title}: {e}")
    return None  # Return None if no results found or an error occurred

# Function to check if an image file exists for a given app title
def image_exists(title):
    # Replace special characters with underscores in the filename
    filename = 'icon/' + title.replace('/', '_').replace(':', '_').replace('|', '_') + '.png'
    filename_scr = 'scrnshot/' + title.replace('/', '_').replace(':', '_').replace('|', '_') + '.png'
    
    # Check if both the icon and screenshot files exist
    if os.path.exists(filename) and os.path.exists(filename_scr):
        return True
    else:
        #print(filename)
        #print(filename_scr)
        return False
        #return True

# Open the JSON file containing app data with UTF-8 encoding
with open('Library.json', 'r', encoding='utf-8') as file:
    json_data = file.read()

# Parse JSON data
data = json.loads(json_data)

# Sort the list by acquisitionTime
sorted_data = sorted(data, key=lambda x: x['libraryDoc'].get('acquisitionTime', ''))

# Set delay between requests (in seconds)
request_delay = 0.3  # Adjust this value as needed

session = requests.Session()
retries = 3

total_apps = len(sorted_data)
with tqdm(total=total_apps) as pbar:
    # Iterate over each app
    screenshot_url=""
    icon_url=""
    for app_item in sorted_data:  # Rename the variable to avoid conflict
        title = app_item['libraryDoc']['doc']['title']
        
        # Check if image file already exists
        if not image_exists(title):
            # Use the title as package name if it starts with a lowercase letter
            if title[0].islower() and '.' in title and ' ' not in title:
                package_name = title
            else:
                # Fetch package name using the app title
                package_name = get_package_name(title)
                
            if package_name is not None:
                # Fetch launcher icon URL
                icon_url = get_icon_url(package_name)
                if icon_url is None:
                    apkpure = get_app_img_apkpure(package_name)
                    if (apkpure is not None):
                        icon_url = apkpure[0]
                        if (screenshot_url is not None):
                            screenshot_url = apkpure[1]
                    #print(icon_url)
                else:
                    screenshot_url = get_first_screenshot_url(package_name)

                if icon_url:
                    # Download the image

                    for _ in range(retries):
                        try:
                            response = session.get(icon_url)
                            response.raise_for_status()  # Raise HTTPError for bad status codes
                        except (ConnectionError, IncompleteRead) as e:
                            print(f"Error downloading image: {e}. Retrying...")
                            time.sleep(5)  # Wait for a moment before retrying
                            print("Failed to download image after retries.")

                    #response = requests.get(icon_url)
                    #response = session.get(icon_url)
                    #if response.status_code == 200:
                    title = title.replace('/', '_').replace(':', '_').replace('|', '_').replace('?', '_')
                    with open(f'icon/{title}.png', 'wb') as img_file:
                         img_file.write(response.content)
                   

                if screenshot_url:
                    # Download the image
                    for _ in range(retries):
                        try:
                            response = session.get(screenshot_url)
                            response.raise_for_status()  # Raise HTTPError for bad status codes
                        except (ConnectionError, IncompleteRead) as e:
                            print(f"Error downloading image: {e}. Retrying...")
                            time.sleep(5)  # Wait for a moment before retrying
                            print("Failed to download image after retries.")

                    #response = requests.get(screenshot_url)
                    #response = session.get(screenshot_url)
                    #if response.status_code == 200:
                    title = title.replace('/', '_').replace(':', '_').replace('|', '_').replace('?', '_')
                    with open(f'scrnshot/{title}.png', 'wb') as img_file:
                        img_file.write(response.content)



                # Introduce a delay between requests
                time.sleep(request_delay)

            else:
                print(f"No package name found for app: {title}")
        # Update progress bar
        pbar.update(1)


# Now you have the images downloaded (or reused), you can create an HTML file
with open('apps_with_icons.html', 'w', encoding='utf-8') as html_file:
    html_file.write('<html><head></head><body>')
    for app_item in sorted_data:  # Rename the variable to avoid conflict
        title = app_item['libraryDoc']['doc']['title']
        try:
            acquisitiontime = app_item['libraryDoc'].get('acquisitionTime')
            try:
                acquisitiontime_obj = datetime.strptime(acquisitiontime, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                acquisitiontime_obj = datetime.strptime(acquisitiontime, "%Y-%m-%dT%H:%M:%SZ")

            acquisitiontime_readable = acquisitiontime_obj.strftime("%d-%m-%Y %H:%M:%S")

            title = title.replace('/', '_').replace(':', '_').replace('|', '_').replace('?', '_')
            
            if image_exists(title):
                html_file.write('<style>')
                html_file.write('.app-container {')
                html_file.write('    display: flex;')
                html_file.write('    border-bottom: 1px solid #ccc;')  # Add border between apps
                html_file.write('}')
                html_file.write('.app-container > div {')
                html_file.write('    flex: 1;')
                html_file.write('    padding: 5px;')
                html_file.write('}')
                html_file.write('</style>')

                html_file.write('<div class="app-container">')
                html_file.write(f'<div><img src="icon/{title}.png" alt="{title}" width="96" height="96"><span>{title}</span></div>')
                html_file.write(f'<div><img src="scrnshot/{title}.png" alt="{title}_screenshot" width="512" height=""><p>{acquisitiontime_readable}</p></div>')
                html_file.write('</div>')
            else:
                print(f"Image file not found for app: {title}")
        except (TypeError) as e:
            print("No acquisition time found")

       


    html_file.write('</body></html>')