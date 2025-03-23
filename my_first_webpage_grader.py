import os
import requests
from bs4 import BeautifulSoup
from utilities import fetch_html, save_to_file, find_heading_for_element

def grade_my_first_webpage(url, student_name, assignment_name):
    feedback = []
    total_score = 40  # Starting from full score

    try:
        # Fetch the website HTML with SSL verification disabled
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

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