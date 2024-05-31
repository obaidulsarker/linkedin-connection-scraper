import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from dotenv import load_dotenv
import os

load_dotenv()

if not os.path.exists(".env"):
    print(".env file not found!")
    exit()

# LinkedIn credentials
username = os.getenv("username")
password = os.getenv("password")

# Initialize WebDriver
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)



# Function to login to LinkedIn
def login_to_linkedin():
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    
    username_input = driver.find_element(By.ID, "username")
    password_input = driver.find_element(By.ID, "password")
    
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.submit()
    time.sleep(5)

# Function to scrape connections
def scrape_connections():
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    time.sleep(5)

    connections = []
    
    while True:
        try:
            # Scroll down the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'scaffold-finite-scroll__load-button')]//span[text()='Show more results']/.."))
            )
            show_more_button.click()
            time.sleep(3)
        except TimeoutException:
            print("No more 'Show more results' button found.")
            break
        except StaleElementReferenceException:
            print("Stale element reference: The page structure changed.")
            continue

    connection_elements = driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card__details")
    for elem in connection_elements:
        try:
            name = elem.find_element(By.CSS_SELECTOR, ".mn-connection-card__name").text
            occupation = elem.find_element(By.CSS_SELECTOR, ".mn-connection-card__occupation").text
            profile_url = elem.find_element(By.XPATH, "../a").get_attribute("href")
            #connection_id = profile_url.split('/')[-1] if profile_url else 'N/A'
            connection_id= profile_url.rstrip('/').split('/')[-1] if profile_url else 'N/A'
            
            connections.append({
                "Name": name,
                "Occupation": occupation,
                "Profile URL": profile_url,
                "ID": connection_id
            })
        except NoSuchElementException as e:
            print(f"An element was not found: {e}")
            continue
    
    return connections

# Function to scrape detailed profile information
def scrape_profile_details(connection_id, profile_url):
    driver.get(profile_url)
    time.sleep(5)
    
    details = {
        'Education': [],
        'Experiences': [],
        'Certifications': [],
        'Contact Info': [],
        'About': [],
        'Skills': []
    }
    
    try:
        education_section = driver.find_element(By.ID, "education-section")
        education_entries = education_section.find_elements(By.CLASS_NAME, "pv-entity__degree-info")
        for entry in education_entries:
            details['Education'].append({
                'ID': connection_id,
                'Education': entry.text
            })
    except NoSuchElementException:
        pass
    
    try:
        experience_section = driver.find_element(By.ID, "experience-section")
        experience_entries = experience_section.find_elements(By.CLASS_NAME, "pv-entity__summary-info")
        for entry in experience_entries:
            details['Experiences'].append({
                'ID': connection_id,
                'Experience': entry.text
            })
    except NoSuchElementException:
        pass
    
    try:
        certification_section = driver.find_element(By.ID, "certifications-section")
        certification_entries = certification_section.find_elements(By.CLASS_NAME, "pv-certification-entity")
        for entry in certification_entries:
            details['Certifications'].append({
                'ID': connection_id,
                'Certification': entry.text
            })
    except NoSuchElementException:
        pass

    try:
        contact_info_button = driver.find_element(By.XPATH, "//a[@data-control-name='contact_see_more']")
        driver.execute_script("arguments[0].click();", contact_info_button)
        time.sleep(3)
        contact_info_section = driver.find_element(By.CLASS_NAME, "pv-contact-info")
        details['Contact Info'].append({
            'ID': connection_id,
            'Contact Info': contact_info_section.text
        })
    except NoSuchElementException:
        pass

    try:
        about_section = driver.find_element(By.ID, "about")
        total_connections = driver.find_element(By.CLASS_NAME, "pv-top-card--list-bullet")
        details['About'].append({
            'ID': connection_id,
            'About': about_section.text,
            'Total Connections': total_connections.text
        })
    except NoSuchElementException:
        pass


    try:
        skills_section = driver.find_element(By.ID, "skills-section")
        skills_entries = skills_section.find_elements(By.CLASS_NAME, "pv-skill-category-entity__name-text")
        for entry in skills_entries:
            details['Skills'].append({
                'ID': connection_id,
                'Skill': entry.text
            })
    except NoSuchElementException:
        pass
    
    return details

# Function to save data to CSV
def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

# Main function
if __name__ == "__main__":
    login_to_linkedin()
    connections = scrape_connections()
    save_to_csv(connections, 'linkedin_connections.csv')

    all_educations = []
    all_experiences = []
    all_certifications = []
    all_contact_info = []
    all_about = []
    all_total_connections = []
    all_skills = []
    
    profile_no = 0
    for connection in connections:
        profile_details = scrape_profile_details(connection['ID'], connection['Profile URL'])
        all_educations.extend(profile_details['Education'])
        all_experiences.extend(profile_details['Experiences'])
        all_certifications.extend(profile_details['Certifications'])
        all_contact_info.extend(profile_details['Contact Info'])
        all_about.extend(profile_details['About'])
        all_skills.extend(profile_details['Skills'])
        time.sleep(3)  # Adding delay to avoid LinkedIn blocking the bot

        profile_no = profile_no + 1
        if profile_no>=10:
            break

    save_to_csv(all_educations, "education.csv")
    save_to_csv(all_experiences, "experiences.csv")
    save_to_csv(all_certifications, "certifications.csv")
    save_to_csv(all_contact_info, "contact_info.csv")
    save_to_csv(all_about, "about.csv")
    save_to_csv(all_skills, "skills.csv")

    driver.quit()
    print("Connections scraped and saved to linkedin_connections.csv")
