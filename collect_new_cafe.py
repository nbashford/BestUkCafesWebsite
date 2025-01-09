"""
File for collecting and storing new cafe data when added by user.
Also formats the data suitable for adding to the database in New Cafes or Cafes.
"""
import time
import os

import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Holds the New Cafe data
new_cafe = {}


def collecting_cafe_data(form):
    """Adds 'add cafe' form data to global new_cafe dictionary. To be used when adding new cafe to db."""
    global new_cafe
    # add all useful form data to dictionary
    form_fields = [field for field in list(form._fields.keys()) if field not in ["submit", "csrf_token"]]
    for field in form_fields:
        new_cafe[field] = form[field].data

    # return new_cafe


def get_lat_long(first_try=True):
    """
    Gets and returns the Latitude and Longitude, from; street address, postcode, town/city, provided in the UK.
    Passes the full address first to openstreetmap api, but if unsuccessful, passes only the postcode to get a
    more approximate address.
    """
    global new_cafe

    latitude = 0
    longitude = 0
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': os.getenv('OSM_USER_AGENT')}

    if first_try:  # full address details
        params = {
            'street': new_cafe['street'],
            'city': new_cafe['city'],
            'country': 'UK',
            'postalcode': new_cafe['postcode'],
            'format': 'json',
            'addressdetails': 1,
        }
    else:  # only pass the postcode for search - less specific
        params = {
            'postalcode': new_cafe['postcode'],
            'format': 'json',
            'addressdetails': 1
        }

    response = requests.get(url, params=params, headers=headers)

    try:
        data = response.json()
        if data:  # extract latitude and longitude
            latitude = data[0]["lat"]
            longitude = data[0]["lon"]

    except requests.exceptions.JSONDecodeError:
        print("Failed to parse JSON. Raw response:")
        print(response.text)

    # issue identifying openstreetmap location from full address
    if latitude == 0 and longitude == 0 and first_try:
        # use just postcode to get lat, lon
        latitude, longitude = get_lat_long(first_try=False)

    return latitude, longitude


def get_opening(open_string_list):
    """
    condenses/reformats the opening times - to reduce the amount of text needed if weekdays or weekend opening
    times are the same - returns open_string list as a single string, with each day opening times separated by '|'
    :param open_string_list: list of opening times for each day, format: "Day: open time"
    :return: string
    """
    print(open_string_list)
    times = [entry.split(": ")[1] for entry in open_string_list]
    weekday_same_time = all(time == times[0] for time in times[:5])
    weekend_same_time = all(time == times[5] for time in times[-2:])

    # if user has not selected any times
    if all("select" in time for time in times):
        open_string = "|".join(open_string_list)
        return open_string

    # weekday is same but weekends not
    if weekday_same_time and not weekend_same_time:
        open_string = f"Monday - Friday: {times[0]}|Saturday: {times[5]}|Sunday: {times[6]}"

    # weekdays same and weekends same
    elif weekday_same_time and weekend_same_time:
        open_string = f"Monday - Friday: {times[0]}|Saturday - Sunday: {times[5]}"

    # weekdays not same but weekend is
    elif not weekend_same_time and weekend_same_time:
        open_string = (f"Monday: {times[0]}|Tuesday: {times[1]}|Wednesday: {times[2]}|Thursday: {times[3]}"
                       f"|Friday: {times[4]}|Saturday - Sunday: {times[5]}")

    # weekdays and weekends not the same
    else:
        open_string = "|".join(open_string_list)

    return open_string


def format_details():
    """
    Formats the user submitted new cafe data to that suitable for entering
    into the NewCafes or Cafes database.
    name, city, street, postcode, wifi, laptop, pets all in suitable format, but this
    gets the latitude and longitude of the cafe address, and formats the opening times string.
    :return: passed cafe_dict dictionary with updated lat and lon, and formatted opening times.
    """
    global new_cafe
    # 1. get the latitude and longitude
    new_cafe['latitude'], new_cafe['longitude'] = get_lat_long()

    # 2. format the opening times string
    opening_times = [
        f"Monday: {new_cafe['monday_morn']}-{new_cafe['monday_eve']}",
        f"Tuesday: {new_cafe['tuesday_morn']}-{new_cafe['tuesday_eve']}",
        f"Wednesday: {new_cafe['wednesday_morn']}-{new_cafe['wednesday_eve']}",
        f"Thursday: {new_cafe['thursday_morn']}-{new_cafe['thursday_eve']}",
        f"Friday: {new_cafe['friday_morn']}-{new_cafe['friday_eve']}",
        f"Saturday: {new_cafe['saturday_morn']}-{new_cafe['saturday_eve']}",
        f"Sunday: {new_cafe['sunday_morn']}-{new_cafe['sunday_eve']}"
        ]
    new_cafe['opening'] = get_opening(opening_times)

    return new_cafe


def clear_new_cafe_saved_details():
    global new_cafe
    new_cafe = {}


"""
These functions below are experimental and can be potentially used for 
another program to automatically search for cafe details i.e. if the cafe exists, 
if the address is different to what the user has inputted. Involves scraping tripadvisor.
"""

def check_tripadvisor(cafe_dict):

    name = cafe_dict['name']
    city = cafe_dict['city']

    title_found = None
    city_found = None
    street_found = None
    postcode_found = None

    firefox_options = Options()
    firefox_options.add_argument("--disable-extensions")
    firefox_options.set_preference("dom.push.enabled", False)  # Disable notifications
    firefox_options.set_preference("dom.popup_maximum", 0)  # Disable all popups
    firefox_options.set_preference("privacy.popups.showBrowser", False)  # Disable popups in the browser
    driver = webdriver.Firefox(options=firefox_options)

    # "https://www.google.co.uk/search?q=if+up+north+leeds+tripadvisor"
    name = name.replace(" ", "+")
    city= city.replace(" ", "+")
    driver.get(f"https://www.google.co.uk/search?q={name}+{city}+tripadvidsor")
    # driver.get(f"https://duckduckgo.com/?q={name}+{city}+tripadvisor")

    try:
        reject_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, '//div[contains(text(), "Accept all")]/ancestor::button')))
    except TimeoutException as e:
        print('No such button')
        time.sleep(5)
    else:
        time.sleep(1)
        reject_button.click()
        time.sleep(3)

    full_page_html = driver.page_source
    soup = BeautifulSoup(full_page_html, 'html.parser')

    all_links = soup.find_all('a')

    links = [link.get('href') for link in all_links]

    tripadvisor_link = None
    for link in links:
        if link and "https://www.tripadvisor.co.uk" in link:
            tripadvisor_link = link
            break

    if tripadvisor_link:
        print("In here")
        driver.get(tripadvisor_link)

        try:
            reject_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.ID, 'onetrust-reject-all-handler')))
        except TimeoutException as e:
            print("reject button not found")
        else:
            time.sleep(1)
            reject_button.click()
            time.sleep(3)

        try:
            load_more = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="lithium-root"]/main/div/div/div[2]/div[3]/div/div[1]/span/h1')))
        except TimeoutException as e:
            print("Page not loaded")
            try:
                load_more = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/main/div/div[3]/div/div[1]/h1")))
            except TimeoutException as e:
                print("Still not found")
            else:
                title_container = driver.find_element(By.XPATH,
                                                      "/html/body/div[1]/main/div/div[3]/div/div[1]/h1")
                address_container = driver.find_element(By.XPATH,
                                                        '/html/body/div[1]/main/div/div[3]/div/div[3]/span[1]/span[2]/button/span/div')

        else:
            title_container = driver.find_element(By.XPATH, '//*[@id="lithium-root"]/main/div/div/div[2]/div[3]/div/div[1]/span/h1')

            address_container = driver.find_element(By.XPATH, '//*[@id="lithium-root"]/main/div/div/div[2]/div[3]/div/div[3]/span[1]/span/div/span')

        title = title_container.text
        title_found = title.strip()
        address = address_container.text


        print(title)
        print(address)

        location_remove = ['England, Scotland, Wales, Northern Ireland']

        for location in location_remove:
            if location in address:
                address.replace(location, "")


        address_full = address.split(", ")

        street_found = address_full[0].strip()

        city_postcode = address_full[1].strip().split(" ")

        postcode_found = " ".join(city_postcode[-2:])

        city_found = " ".join(city_postcode[:-2])

        print(title_found)
        print(street_found)
        print(city_found)
        print(postcode_found)

    return title_found, street_found, city_found, postcode_found


def is_cafe(cafe_dict):

    cafe_exists = False
    errors = []

    url = "https://api.company-information.service.gov.uk/search/companies"

    # Use HTTPBasicAuth
    auth = HTTPBasicAuth(os.getenv("GOV_COMPANY_SERVICE_KEY"), '')

    params = {
        'q': cafe_dict['name']
    }

    response = requests.get(url, params=params, auth=auth)
    print("Response Status Code:", response.status_code)

    if response.ok:

        data = response.json()
        print(data)

        title = data['items'][0]['title'].title()
        street = data['items'][0]['address']['address_line_1']
        city = data['items'][0]['address']['locality']
        postcode = data['items'][0]['address']['postal_code']
        still_active = True if data['items'][0]['company_status'] == 'active' else False


        def check_is_valid(cafe_dict, title, city, postcode):

            exists = False
            error_list = []

            if cafe_dict['name'] == title:
                exists = True
            else:
                orig_name_set = set(cafe_dict['name'].title())
                actual_name_set = set(title)
                if orig_name_set.issubset(actual_name_set):
                    orig_town_set = set(cafe_dict['city'])
                    actual_city_set = city
                    if orig_town_set.issubset(actual_city_set):
                        exists = True
                    else:
                        error_list.append("City/Town seems incorrect")
                    if cafe_dict['postcode'].lower().replace(" ", "") == postcode.lower().replace(" ", ""):
                        exists = True
                    else:
                        error_list.append("Postcode seems incorrect")

                error_list.append("Cafe Name seems incorrect")

            return exists, error_list

        cafe_exists, errors = check_is_valid(cafe_dict, title, city, postcode)

        if not cafe_exists:

            title, street, city, postcode = check_tripadvisor(cafe_dict)

            if title and street and city and postcode:

                cafe_exists, errors = check_is_valid(cafe_dict, title, city, postcode)

        if cafe_exists:

            cafe_dict['name'] = title
            cafe_dict['street'] = street
            cafe_dict['city'] = city
            cafe_dict['postcode'] = postcode


    return cafe_dict, True if cafe_exists else False, errors






