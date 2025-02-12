import os
import requests
from bs4 import BeautifulSoup

from utilities import fetch_html, save_to_file

def grade_my_second_webpage(url, student_name, assignment_name):
    feedback = []
    total_score = 40  # Starting from full score

    try:
        # Fetch the website HTML with SSL verification disabled
        content = fetch_html(url)
        soup = BeautifulSoup(content, 'html.parser')

        # Save the pulled HTML to a file for inspection
        html_filename = f"{student_name}_{assignment_name}.html"
        html_file_path = os.path.join("pulled_html", html_filename)
        save_to_file(content, html_file_path)

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