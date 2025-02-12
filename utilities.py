# Import necessary libraries
import os
import zipfile
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests
import urllib3
import pandas as pd

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

fetched_pages_path = ""

def grading_setup(uploaded_file_path, results_path):
    # Ensure the extraction directory exists
    os.makedirs(results_path, exist_ok=True)

    # Create a directory to store pulled HTML files
    pulled_html_path = os.path.join(results_path, "pulled_html")
    os.makedirs(pulled_html_path, exist_ok=True)

    # Create a directory for storing fetched webpages
    fetched_pages_path = os.path.join(results_path, "fetched_pages")
    os.makedirs(fetched_pages_path, exist_ok=True)

    # Create a directory for CSV results
    fetched_pages_path = os.path.join(results_path, "csv")
    os.makedirs(fetched_pages_path, exist_ok=True)

    extract_zip(uploaded_file_path, pulled_html_path)

    # Get a list of extracted files
    extracted_files = os.listdir(pulled_html_path)
    return extracted_files

# Ensure the extraction directory exists
def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

# Extract files from a zip archive
def extract_zip(uploaded_file_path, extraction_path):
    with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
        zip_ref.extractall(extraction_path)

# Validate if a given URL is valid
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

# Extract URL from an HTML file
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
    if url and not is_valid_url(url):
        raise ValueError(f"Invalid URL extracted: {url}")
    return url

# Check if a URL points to a local IP address
def is_local_url(url):
    return "localhost" in url or "127.0.0.1" in url

# Find a heading (h1 to h6) before a given element in an HTML document
def find_heading_for_element(soup, element):
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for heading in reversed(headings):
        if heading.find_next() == element:
            return True
    return False

# Fetch and parse HTML content from a URL
def fetch_html(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()  # Raise an error for HTTP issues
    return response.text

# Save content to a file
def save_to_file(content, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

# Function to validate URLs
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

# Function to check if the URL is pointing to a local IP address
def is_local_url(url):
    return "localhost" in url or "127.0.0.1" in url

def grade_extracted_files(grading_function, results_path, extracted_files, assignment_name):
    # Grading the extracted files
    grading_results = {}
    grading_tuples = []  # To hold tuples of (student_name, score, feedback)
    late_assignments = []  # To hold late assignments separately
    for file_name in extracted_files:
        pulled_path = os.path.join(results_path,"pulled_html")
        file_path = os.path.join(pulled_path, file_name)

        # Skip directories to avoid issues
        if os.path.isdir(file_path):
            continue

        # Determine if the file is marked as late
        is_late = "_LATE_" in file_name

        # Extract URL from the HTML file
        try:
            url = extract_url_from_html(file_path)
            student_name = file_name.split('_')[0]
            if not url:
                feedback = "No valid URL found in the submission. Please resubmit with a valid URL."
                grading_results[file_name] = {
                    'Score': 1,
                    'Feedback': feedback
                }
                if is_late:
                    late_assignments.append((student_name, 0, feedback))
                else:
                    grading_tuples.append((student_name, 0, feedback))
                continue

            # Check if the URL is local
            if is_local_url(url):
                feedback = f"Submitted a URL pointing to a local IP address ({url}). Please resubmit with a valid online URL."
                grading_results[file_name] = {
                    'Score': 1,
                    'Feedback': feedback
                }
                if is_late:
                    late_assignments.append((student_name, 1, feedback))
                else:
                    grading_tuples.append((student_name, 1, feedback))
                continue
            
            fetched_pages_path = os.path.join(results_path,"fetched_pages")
            full_file_path = os.path.join(fetched_pages_path, f"{student_name}_{assignment_name}.html")
            fetch_and_save_html(url, full_file_path)

            # Grade the website and save HTML
            score, feedback = grading_function(url, student_name, assignment_name)
            grading_results[file_name] = {
                'Score': score,
                'Feedback': "; ".join(feedback) if feedback else "Good job!"
            }
            if is_late:
                late_assignments.append((student_name, score, "; ".join(feedback) if feedback else "Good job!"))
            else:
                grading_tuples.append((student_name, score, "; ".join(feedback) if feedback else "Good job!"))
        except (UnicodeDecodeError, ValueError) as e:
            feedback = f"Error processing file: {str(e)}"
            grading_results[file_name] = {
                'Score': 1,
                'Feedback': feedback
            }
            if is_late:
                late_assignments.append((file_name, 1, feedback))
            else:
                grading_tuples.append((file_name, 1, feedback))
    # Sort the grading tuples alphabetically, keeping late assignments at the end
    grading_tuples.sort()
    late_assignments.sort()
    grading_tuples.extend(late_assignments)
    
    # Convert grading results to a DataFrame
    grading_results_df = pd.DataFrame.from_dict(grading_results, orient='index')

    grading_path = os.path.join(results_path, "csv")
    os.makedirs(grading_path, exist_ok=True)
    # Save results to a CSV file
    grading_results_csv_path = os.path.join(grading_path, 'grading_results.csv')
    grading_results_df.to_csv(grading_results_csv_path)

    print(f"Grading results saved to: {grading_results_csv_path}")
    return grading_tuples

# Function to fetch and save HTML content
def fetch_and_save_html(url, save_path):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text
        
        save_to_file(content, save_path)
        return content
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch content from the URL: {e}")