# Import necessary libraries for extraction, parsing, and grading
import zipfile
import os
import pandas as pd
from bs4 import BeautifulSoup

# Define the path to the uploaded zip file and the extraction directory
uploaded_file_path = input("Path to submissions zip file: ")
extraction_path = input("Path to results folder: ")

# Ensure the extraction directory exists
os.makedirs(extraction_path, exist_ok=True)

# Extract the files from the zip archive
with zipfile.ZipFile(uploaded_file_path, 'r') as zip_ref:
    zip_ref.extractall(extraction_path)

# Get a list of extracted files
extracted_files = os.listdir(extraction_path)

# Function to check if the file contains a URL (meta refresh or anchor tag)
def is_url_submission(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check for meta refresh or <a href> with a URL
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'Refresh'})
    anchor_tag = soup.find('a', href=True)
    
    if meta_refresh:
        url = meta_refresh.get('content').split('url=')[-1].strip()
        return True, url
    elif anchor_tag:
        url = anchor_tag.get('href')
        return True, url
    return False, None

# Function to grade an individual HTML file
def grade_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    feedback = []
    total_score = 20  # Starting from full score
    
    # Criteria 1: Check for at least 3 different heading tags, horizontal rule, and paragraph tag
    heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    unique_headings = set(tag.name for tag in heading_tags)
    hr_tag = soup.find('hr')
    p_tag = soup.find('p')
    
    required_elements = 0
    if len(unique_headings) >= 3:
        required_elements += 1
    else:
        feedback.append("Fewer than 3 different heading tags found.")
        total_score -= 5  # Deduct 5 points for missing headings
    
    if hr_tag:
        required_elements += 1
    else:
        feedback.append("Missing horizontal rule.")
        total_score -= 5  # Deduct 5 points for missing horizontal rule
    
    if p_tag:
        required_elements += 1
    else:
        feedback.append("Missing paragraph tag.")
        total_score -= 5  # Deduct 5 points for missing paragraph tag
    
    # Criteria 2: Check for basic structure tags & indentation
    doctype_present = '<!DOCTYPE' in content.upper()
    html_tag = soup.find('html')
    head_tag = soup.find('head')
    body_tag = soup.find('body')
    
    basic_elements = sum([doctype_present, bool(html_tag), bool(head_tag), bool(body_tag)])
    
    if basic_elements < 4:
        missing_elements = []
        if not doctype_present:
            missing_elements.append('<!DOCTYPE>')
        if not html_tag:
            missing_elements.append('<html>')
        if not head_tag:
            missing_elements.append('<head>')
        if not body_tag:
            missing_elements.append('<body>')
        feedback.append(f"Missing basic structure elements: {', '.join(missing_elements)}.")
        total_score -= 5  # Deduct 5 points for missing any basic structure elements
    else:
        # Simplified indentation check
        lines = content.split('\n')
        has_indentation = any(len(line) - len(line.lstrip()) > 0 for line in lines if line.strip())
        if not has_indentation:
            feedback.append("No indentation found in the file.")
            total_score -= 5  # Deduct 5 points for missing indentation
    
    # Ensure total score doesn't go below zero
    total_score = max(total_score, 0)
    
    # Return the score and feedback
    return total_score, feedback

# Grading the extracted files
grading_results = {}
for file_name in extracted_files:
    file_path = os.path.join(extraction_path, file_name)

    # Check if the file is an image
    if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        grading_results[file_name] = {
            'Score': 1,
            'Feedback': "Submitted an image. Please resubmit the assignment with the proper HTML file."
        }
        continue

    # Check if the file is an HTML file
    if file_name.endswith('.html'):
        # Check if the file contains a URL submission
        is_url, url_content = is_url_submission(file_path)
        if is_url:
            if "localhost" in url_content or "127.0.0.1" in url_content:
                grading_results[file_name] = {
                    'Score': 1,
                    'Feedback': f"Submitted a URL pointing to a local IP address ({url_content}). Please resubmit the assignment with the proper HTML file."
                }
                continue
            else:
                grading_results[file_name] = {
                    'Score': 1,
                    'Feedback': f"Submitted a URL ({url_content}). Please resubmit the assignment with the proper HTML file."
                }
                continue

        # Grade the HTML file
        score, feedback = grade_html_file(file_path)
        grading_results[file_name] = {
            'Score': score,
            'Feedback': "; ".join(feedback) if feedback else "Good job!"
        }

# Convert grading results to a DataFrame
grading_results_df = pd.DataFrame.from_dict(grading_results, orient='index')

# Save results to a CSV file
grading_results_csv_path = os.path.join(extraction_path, 'grading_results.csv')
grading_results_df.to_csv(grading_results_csv_path)

print(f"Grading results saved to: {grading_results_csv_path}")
