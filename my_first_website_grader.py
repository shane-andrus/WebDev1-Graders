# Import necessary libraries for extraction, fetching, and grading HTML
import zipfile
import os
import pandas as pd
from bs4 import BeautifulSoup
import auto_canvas
import requests
from urllib.parse import urljoin, urlparse
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the path to the uploaded zip file and the extraction directory
uploaded_file_path = input("Path to submissions zip file: ")
extraction_path = input("Path to results folder: ")

# Ensure the extraction directory exists
os.makedirs(extraction_path, exist_ok=True)

# Create a directory for grading results
grading_results_path = os.path.join(extraction_path, "grading_results")
os.makedirs(grading_results_path, exist_ok=True)

# Create a directory for storing fetched webpages
fetched_pages_path = os.path.join(extraction_path, "fetched_pages")
os.makedirs(fetched_pages_path, exist_ok=True)

# Extract the files from the zip archive
with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
    zip_ref.extractall(extraction_path)

# Get a list of extracted files
extracted_files = os.listdir(extraction_path)

# Function to extract URL from HTML file
def extract_url_from_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    url = None

    # Extract URL from <meta> or <a>
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'Refresh'})
    if meta_refresh:
        url = meta_refresh.get('content').split('url=')[-1].strip()

    anchor_tag = soup.find('a', href=True)
    if anchor_tag:
        url = anchor_tag['href']

    # Validate URL
    if url and not urlparse(url).scheme:
        raise ValueError(f"Invalid URL extracted: {url}")

    # Check for local or 127.0.0.1 address
    if "localhost" in url or "127.0.0.1" in url:
        raise ValueError(f"Invalid URL: Points to a local address ({url}).")

    return url

# Function to fetch and save HTML content
def fetch_and_save_html(url, save_path):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(content)

        return content
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch content from the URL: {e}")

# Recursive function to fetch all linked pages
def fetch_all_linked_pages(base_url, current_content, folder_path, visited_urls):
    soup = BeautifulSoup(current_content, 'html.parser')
    internal_links = [link['href'] for link in soup.find_all('a', href=True) if not link['href'].startswith(('http://', 'https://', '/'))]
    for relative_link in internal_links:
        full_url = urljoin(base_url, relative_link)
        if full_url not in visited_urls:
            visited_urls.add(full_url)
            linked_page_path = os.path.join(folder_path, "linked.html")
            try:
                linked_content = fetch_and_save_html(full_url, linked_page_path)
                fetch_all_linked_pages(full_url, linked_content, folder_path, visited_urls)
            except ValueError as e:
                print(f"Failed to fetch linked page: {relative_link} - {e}")

# Function to grade an individual submission
def grade_html_file(url, file_path, submission_folder):
    feedback = []
    total_score = 20  # Maximum score for the assignment

    try:
        # Fetch the main page HTML content
        main_page_path = os.path.join(submission_folder, "main_page.html")
        main_content = fetch_and_save_html(url, main_page_path)
        visited_urls = {url}

        # Fetch all linked pages
        fetch_all_linked_pages(url, main_content, submission_folder, visited_urls)

        # Grade internal and external links for the main and linked pages
        total_internal_links = 0
        has_external_image_link = False

        # Analyze the main page
        soup = BeautifulSoup(main_content, 'html.parser')
        internal_links_main = [link['href'] for link in soup.find_all('a', href=True) if not link['href'].startswith(('http://', 'https://', '/'))]
        total_internal_links += len(internal_links_main)

        images_in_links_main = [a for a in soup.find_all('a', href=True) if a.find('img') and a['href'].startswith(('http://', 'https://')) and a.get('target') == '_blank']
        if images_in_links_main:
            has_external_image_link = True

        # Analyze the linked page
        linked_page_path = os.path.join(submission_folder, "linked.html")
        if os.path.exists(linked_page_path):
            with open(linked_page_path, 'r', encoding='utf-8') as linked_file:
                linked_content = linked_file.read()
            linked_soup = BeautifulSoup(linked_content, 'html.parser')

            internal_links_linked = [link['href'] for link in linked_soup.find_all('a', href=True) if not link['href'].startswith(('http://', 'https://', '/'))]
            total_internal_links += len(internal_links_linked)

            linked_images_in_links = [a for a in linked_soup.find_all('a', href=True) if a.find('img') and a['href'].startswith(('http://', 'https://')) and a.get('target') == '_blank']
            if linked_images_in_links:
                has_external_image_link = True

        # Check for total internal links
        if total_internal_links < 2:
            feedback.append("The submission must have at least 2 internal links across all pages.")
            total_score -= 5

        # Check for at least one image surrounded by an <a> tag pointing to an external site with target="_blank"
        if not has_external_image_link:
            feedback.append("The submission must have at least one <img> tag surrounded by an <a> tag pointing to an external site with target=\"_blank\".")
            total_score -= 5

    except ValueError as e:
        feedback.append(str(e))
        total_score = 0

    # Ensure the total score is not negative
    total_score = max(total_score, 0)

    return total_score, feedback

# Grading the extracted files
grading_results = {}
for file_name in extracted_files:
    file_path = os.path.join(extraction_path, file_name)

    # Skip non-HTML files
    if not file_name.endswith('.html'):
        continue

    try:
        # Extract the URL from the HTML file
        url = extract_url_from_html(file_path)
        if not url:
            raise ValueError("No valid URL found in the file.")

        # Create a directory for the student's submission
        student_name = os.path.splitext(file_name)[0]
        student_folder = os.path.join(fetched_pages_path, student_name)
        os.makedirs(student_folder, exist_ok=True)

        # Grade the HTML file
        score, feedback = grade_html_file(url, file_path, student_folder)
        grading_results[file_name] = {
            'Score': score,
            'Feedback': "; ".join(feedback)
        }

    except Exception as e:
        grading_results[file_name] = {
            'Score': 1,
            'Feedback': str(e)
        }

# Convert grading results to a DataFrame
grading_results_df = pd.DataFrame.from_dict(grading_results, orient='index')

# Save results to a CSV file
grading_results_csv_path = os.path.join(grading_results_path, 'grading_results.csv')
grading_results_df.to_csv(grading_results_csv_path)

print(f"Grading results saved to: {grading_results_csv_path}")

# Optionally, push grades to Canvas
auto_canvas.putGradesIn([(file_name.split('_')[0], result['Score'], result['Feedback']) for file_name, result in grading_results.items()])
