# Import necessary libraries for extraction, fetching, and grading HTML
import zipfile
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import auto_canvas
import urllib3

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

# Create a directory for grading results
grading_results_path = os.path.join(extraction_path, "grading_results")
os.makedirs(grading_results_path, exist_ok=True)

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

    # Check for <meta http-equiv="Refresh"> tag
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'Refresh'})
    if meta_refresh:
        url = meta_refresh.get('content').split('url=')[-1].strip()
        return url

    # Check for <a href> tag
    anchor_tag = soup.find('a', href=True)
    if anchor_tag:
        return anchor_tag['href']

    return None

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

        # 1. Basic structure and indentation (3 pts)
        doctype_present = '<!DOCTYPE' in content.upper()
        html_tag = soup.find('html')
        head_tag = soup.find('head')
        body_tag = soup.find('body')

        basic_elements = sum([doctype_present, bool(html_tag), bool(head_tag), bool(body_tag)])
        if basic_elements < 4:
            feedback.append("Missing one or more basic structure elements: <!DOCTYPE>, <html>, <head>, <body>.")
            total_score -= 2
        else:
            lines = content.split('\n')
            has_indentation = any(len(line) - len(line.lstrip()) > 0 for line in lines if line.strip())
            if not has_indentation:
                feedback.append("No indentation found in the file.")
                total_score -= 1

        # 2. Heading for favorite cereal, horizontal rule, paragraph (6 pts)
        h1_tag = soup.find('h1')
        hr_tag = soup.find('hr')
        p_tag = soup.find('p')
        if not h1_tag or not hr_tag or not p_tag:
            feedback.append("Missing a heading for the favorite cereal, a horizontal rule, or a paragraph describing it.")
            total_score -= 3

        # 3. Validate unordered list for cereal features
        ul_tag = soup.find('ul')
        ul_items = ul_tag.find_all('li') if ul_tag else []
        if not ul_tag or len(ul_items) < 3:
            feedback.append("Missing an unordered list describing features of the favorite cereal or fewer than 3 items.")
            total_score -= 4

        # 4. Validate ordered list for favorite cereals
        ol_tag = soup.find('ol')
        ol_items = ol_tag.find_all('li') if ol_tag else []
        if not ol_tag or len(ol_items) < 3:
            feedback.append("Missing an ordered list ranking favorite cereals or fewer than 3 items.")
            total_score -= 4

        # 5. Validate image heading and attributes
        img_tags = soup.find_all('img')
        valid_images = [img for img in img_tags if img.get('alt')]
        has_heading_before_image = any(find_heading_for_element(soup, img) for img in img_tags)

        if not valid_images or not has_heading_before_image:
            feedback.append("Missing a relevant heading for the cereal image or the image does not include an alt attribute.")
            total_score -= 4

    except requests.exceptions.RequestException as e:
        feedback.append(f"Failed to fetch website: {e}")
        total_score = 1  # No score if the website can't be fetched

    # Ensure total score doesn't go below zero
    total_score = max(total_score, 0)

    # Return the score and feedback
    return total_score, feedback

# Grading the extracted files
grading_results = {}
grading_tuples = []  # To hold tuples of (student_name, score, feedback)

for file_name in extracted_files:
    file_path = os.path.join(extraction_path, file_name)

    # Skip directories to avoid issues
    if os.path.isdir(file_path):
        continue

    # Extract URL from the HTML file
    try:
        url = extract_url_from_html(file_path)
        if not url:
            feedback = "No valid URL found in the submission. Please resubmit with a valid URL."
            grading_results[file_name] = {
                'Score': 1,
                'Feedback': feedback
            }
            student_name = file_name.split('_')[0]
            grading_tuples.append((student_name, 0, feedback))
            continue

        # Check if the URL is local
        if is_local_url(url):
            feedback = f"Submitted a URL pointing to a local IP address ({url}). Please resubmit with a valid online URL."
            grading_results[file_name] = {
                'Score': 1,
                'Feedback': feedback
            }
            student_name = file_name.split('_')[0]
            grading_tuples.append((student_name, 1, feedback))
            continue

        # Grade the website
        student_name = file_name.split('_')[0]
        assignment_name = "myfirstwebpage"

        score, feedback = grade_website(url, student_name, assignment_name)
        grading_results[file_name] = {
            'Score': score,
            'Feedback': "; ".join(feedback) if feedback else "Good job!"
        }
        grading_tuples.append((student_name, score, "; ".join(feedback) if feedback else "Good job!"))

    except Exception as e:
        feedback = f"Error processing file: {str(e)}"
        grading_results[file_name] = {
            'Score': 1,
            'Feedback': feedback
        }
        student_name = file_name.split('_')[0]
        grading_tuples.append((student_name, 0, feedback))

# Convert grading results to a DataFrame
grading_results_df = pd.DataFrame.from_dict(grading_results, orient='index')

# Save results to a CSV file
grading_results_csv_path = os.path.join(grading_results_path, 'grading_results.csv')
grading_results_df.to_csv(grading_results_csv_path)

print(f"Grading results saved to: {grading_results_csv_path}")

# Pass the grading tuples to the auto canvas function
auto_canvas.putGradesIn(grading_tuples)