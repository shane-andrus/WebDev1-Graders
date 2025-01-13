# Import necessary libraries for extraction, fetching, and grading HTML
import zipfile
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urlparse
import logging
import auto_canvas

# Configure logging
logging.basicConfig(level=logging.INFO)

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the path to the uploaded zip file and the extraction directory
uploaded_file_path = input("Path to submissions zip file: ")
extraction_path = input("Path to results folder: ")

# Ensure the extraction directory exists
os.makedirs(extraction_path, exist_ok=True)

# Create a directory to store pulled HTML files
pulled_html_path = os.path.join(extraction_path, "pulled_html")
os.makedirs(pulled_html_path, exist_ok=True)

# Extract the files from the zip archive
with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
    zip_ref.extractall(extraction_path)

# Get a list of extracted files
extracted_files = os.listdir(extraction_path)

# Function to validate URLs
def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

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
    if url and not is_valid_url(url):
        raise ValueError(f"Invalid URL extracted: {url}")
    return url

# Function to check if the URL is pointing to a local IP address
def is_local_url(url):
    return "localhost" in url or "127.0.0.1" in url

# Detect heading before element
def find_heading_for_element(soup, element):
    """Finds a heading (h1 to h6) that appears before a given element."""
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for heading in reversed(headings):
        if heading.find_next() == element:
            return True
    return False

# Function to grade the website
def grade_website(url, student_name, assignment_name):
    feedback = []
    total_score = 40  # Starting from full score

    try:
        # Fetch the website HTML with SSL verification disabled
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an error for HTTP issues
        content = response.text

        # Save the pulled HTML to a file for inspection
        html_filename = f"{student_name}_{assignment_name}.html"
        html_file_path = os.path.join(pulled_html_path, html_filename)
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(content)

        soup = BeautifulSoup(content, 'html.parser')

        # 1. File structure (4 pts)
        missing_tags = []
        doctype_present = '<!DOCTYPE' in content.upper()
        html_tag = soup.find('html')
        head_tag = soup.find('head')
        body_tag = soup.find('body')

        if not doctype_present:
            missing_tags.append("<!DOCTYPE>")
        if not html_tag:
            missing_tags.append("<html>")
        if not head_tag:
            missing_tags.append("<head>")
        if not body_tag:
            missing_tags.append("<body>")

        if missing_tags:
            feedback.append(f"Missing structure elements: {', '.join(missing_tags)}.")
            total_score -= 4

        # 2. HTML content (12 pts)
        html_content_issues = []
        h1_tag = soup.find('h1')
        hr_tag = soup.find('hr')
        p_tag = soup.find('p')
        smaller_headings = soup.find_all(['h2', 'h3'])
        ul_tag = soup.find('ul')
        ol_tag = soup.find('ol')

        if not h1_tag:
            html_content_issues.append("Missing largest heading (<h1>).")
        if not hr_tag:
            html_content_issues.append("Missing horizontal rule (<hr>).")
        if not p_tag:
            html_content_issues.append("Missing paragraph (<p>).")
        if len(smaller_headings) < 2:
            html_content_issues.append("Fewer than 2 smaller headings (<h2> or <h3>).")
        if not ul_tag:
            html_content_issues.append("Missing unordered list (<ul>).")
        if not ol_tag:
            html_content_issues.append("Missing ordered list (<ol>).")

        if html_content_issues:
            feedback.append(f"HTML content issues: {', '.join(html_content_issues)}.")
            total_score -= min(6, len(html_content_issues) * 2)  # Deduct 2 points per issue, capped at 6.

        # 3. Images (12 pts)
        img_tags = soup.find_all('img')
        valid_images = [img for img in img_tags if img.get('alt')]
        border_image = any("border" in (img.get('src') or "").lower() for img in img_tags)
        youtube_logo = any("youtube" in (img.get('src') or "").lower() and img.get('width') == "80px" for img in img_tags)

        if len(valid_images) < 3:
            feedback.append(f"Missing alt attributes or fewer than 3 images have alt attributes. Found: {len(valid_images)}.")
            total_score -= 4
        if not border_image:
            feedback.append("Missing border image.")
            total_score -= 2
        if not youtube_logo:
            feedback.append("Missing YouTube logo with correct size (80px width).")
            total_score -= 2

        # 4. Inline styles (12 pts)
        style_issues = []
        body_style = soup.body.get('style', '').lower() if soup.body else ""
        has_background_color = "background-color" in body_style
        heading_styles = [tag.get('style', '').lower() for tag in soup.find_all(['h1', 'h2', 'h3'])]
        list_styles = [ul_tag.get('style', '').lower() if ul_tag else "", ol_tag.get('style', '').lower() if ol_tag else ""]
        border_styles = [tag.get('style', '').lower() for tag in soup.find_all(True) if "border" in (tag.get('style', '').lower())]

        if not has_background_color:
            style_issues.append("Missing background color style on <body>.")
        if len(heading_styles) < 3:
            style_issues.append("Fewer than 3 headings (<h1>, <h2>, <h3>) have inline styles.")
        if not any(list_styles):
            style_issues.append("Lists (<ul> or <ol>) are missing styles.")
        if len(border_styles) < 2:
            style_issues.append("Fewer than 2 elements use border property.")

        if style_issues:
            feedback.append(f"Inline style issues: {', '.join(style_issues)}.")
            total_score -= min(6, len(style_issues) * 2)  # Deduct 2 points per issue, capped at 6.

    except requests.exceptions.RequestException as e:
        feedback.append(f"Failed to fetch website: {e}")
        total_score = 0  # No score if the website can't be fetched

    # Ensure total score doesn't go below zero
    total_score = max(total_score, 0)

    # Return the score and feedback
    return total_score, feedback

# Grading the extracted files
grading_results = {}
grading_tuples = []  # To hold tuples of (student_name, score, feedback)
late_assignments = []  # To hold late assignments separately
for file_name in extracted_files:
    file_path = os.path.join(extraction_path, file_name)

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

        # Extract student and assignment information for naming
        
        assignment_name = "mysecondwebpage"

        # Grade the website and save HTML
        score, feedback = grade_website(url, student_name, assignment_name)
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
            'Score': 0,
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

# Save results to a CSV file
grading_results_csv_path = os.path.join(extraction_path, 'grading_results.csv')
grading_results_df.to_csv(grading_results_csv_path)

print(f"Grading results saved to: {grading_results_csv_path}")
print(f"Pulled HTML files saved to: {pulled_html_path}")

auto_canvas.putGradesIn(grading_tuples)


