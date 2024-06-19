import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_disease_links(base_url):
    response = requests.get(base_url)
    if response.status_code != 200:
        logger.error(f"Failed to retrieve the page: {base_url}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    disease_links = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '/diseases/' in href:
            disease_name = a_tag.text.strip()
            disease_url = f"https://www.1mg.com{href}"
            disease_links.append({"name": disease_name, "url": disease_url})

    return disease_links


def extract_section(soup, section_title):
    section = soup.find('h2', string=section_title)
    if section:
        content = section.find_next_sibling('div')
        return content.get_text(separator='\n').strip() if content else None
    return None


def scrape_disease_details(disease):
    url = disease['url']
    disease_name = disease['name']

    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to retrieve the page: {url}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    details = {
        "Disease Name": disease_name,
        "Overview": extract_section(soup, 'Overview'),
        "Key Facts": extract_section(soup, 'Key Facts'),
        "Symptoms": extract_section(soup, 'Symptoms'),
        "Causes": extract_section(soup, 'Causes'),
        "Types": extract_section(soup, 'Types'),
        "Risk Factors": extract_section(soup, 'Risk Factors'),
        "Diagnosis": extract_section(soup, 'Diagnosis'),
        "Prevention": extract_section(soup, 'Prevention'),
        "Specialist to Visit": extract_section(soup, 'Specialist to Visit'),
        "Treatment": extract_section(soup, 'Treatment'),
        "Home-care": extract_section(soup, 'Home-care'),
        "Alternative Therapies": extract_section(soup, 'Alternative Therapies'),
        "Living with": extract_section(soup, 'Living with'),
        "FAQs": [],
        "References": []
    }

    # Extract FAQs
    faq_section = soup.find('h2', string='FAQs')
    if faq_section:
        faqs = []
        for faq in faq_section.find_next_siblings('div', class_='faq'):
            question = faq.find('div', class_='faq-question').text.strip()
            answer = faq.find('div', class_='faq-answer').text.strip()
            faqs.append({"question": question, "answer": answer})
        details["FAQs"] = faqs

    # Extract references
    reference_section = soup.find('h2', string='References')
    if reference_section:
        references = [a['href'] for a in reference_section.find_next_siblings('a', href=True)]
        details["References"] = references

    return details


def print_csv_content(file_path):
    df = pd.read_csv(file_path)
    print(df)


def main():
    base_url = "https://www.1mg.com/all-diseases"

    logger.info("Fetching disease links...")
    disease_links = get_disease_links(base_url)

    if not disease_links:
        logger.error("No disease links found. Exiting.")
        return

    all_disease_details = []
    for disease in disease_links:
        logger.info(f"Scraping details for {disease['name']}...")
        details = scrape_disease_details(disease)
        if details:
            all_disease_details.append(details)
        time.sleep(1)  # Be polite and do not hammer the server

    if not all_disease_details:
        logger.error("No disease details scraped. Exiting.")
        return

    # Save to JSON
    with open('diseases.json', 'w') as f:
        json.dump(all_disease_details, f, indent=4)

    # Save to CSV
    df = pd.DataFrame(all_disease_details)
    csv_file = 'diseases.csv'
    df.to_csv(csv_file, index=False)

    logger.info("Scraping completed and data saved!")

    # Print the CSV content to the terminal
    print_csv_content(csv_file)


if __name__ == "__main__":
    main()
