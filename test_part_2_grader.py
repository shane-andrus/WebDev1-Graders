from bs4 import BeautifulSoup
import requests
import re

# Function to grade an HTML test part 2 assignment
def grade_html_test_part_2(url, student_name, assignment_name):
    feedback = []
    total_score = 0  # Maximum score based on rubric

    try:
        # Fetch the website HTML with SSL verification disabled
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        # Extract internal styles
        internal_styles = soup.find('style')
        internal_styles_content = internal_styles.text if internal_styles else ""

        def check_styles(tag):
            return tag.get('style') or any(tag.get('class') and class_name in internal_styles_content for class_name in tag.get('class', []))

        # Task 1: Theme selection & page setup (4 pts)
        task_score = 4
        if not '<!DOCTYPE html>' in content:
            feedback.append("Missing correct HTML5 doctype.")
            task_score -= 2
        if not soup.find('title'):
            feedback.append("Missing title tag or it is incorrect.")
            task_score -= 2
        total_score += max(0, task_score)

        # Task 2: Header with Hyperlinks (6 pts)
        task_score = 6
        headers = soup.find_all(['h1', 'h2', 'h3'])
        links = [a for a in soup.find_all('a', href=True) if a.get('target') == '_blank']
        if not headers:
            feedback.append("Missing proper header formatting (h1, h2, or h3).")
            task_score -= 3
        if len(links) < 2:
            feedback.append("Missing required hyperlinks that open in a new tab.")
            task_score -= 3
        total_score += max(0, task_score)

        # Task 3: Styled Table with Content (10 pts)
        task_score = 10
        table = soup.find('table')
        if not table:
            feedback.append("Missing table.")
            task_score = 0
        else:
            rows = table.find_all('tr')
            cells = table.find_all('td')
            if len(rows) < 4:
                feedback.append("Table must have at least 4 rows.")
                task_score -= 3
            if len(cells) < 12:
                feedback.append("Table must have at least 12 cells.")
                task_score -= 3
            if not check_styles(table):
                feedback.append("Table lacks necessary styling (inline or internal styles missing).")
                task_score -= 4
        total_score += max(0, task_score)

        # Task 4: Image with Styles (6 pts)
        task_score = 6
        image = soup.find('img')
        if not image:
            feedback.append("Missing image.")
            task_score = 0
        elif not image.get('src'):
            feedback.append("Image source is missing.")
            task_score -= 3
        elif not check_styles(image):
            feedback.append("Image lacks required styling (inline or internal styles missing).")
            task_score -= 3
        total_score += max(0, task_score)

        # Task 5: Lists & Horizontal Rule (10 pts)
        task_score = 10
        lists = soup.find_all(['ul', 'ol'])
        hr = soup.find('hr')
        if len(lists) < 2:
            feedback.append("Missing required lists (one numbered and one bulleted list).")
            task_score -= 5
        if not hr:
            feedback.append("Missing horizontal rule for content separation.")
            task_score -= 5
        total_score += max(0, task_score)

        # Task 6: Concluding Paragraph (5 pts)
        task_score = 5
        paragraphs = soup.find_all('p')
        long_paragraphs = [p for p in paragraphs if len(p.text.split()) >= 5]
        if not long_paragraphs:
            feedback.append("Concluding paragraph is missing or too short (must be at least 5 sentences).")
            task_score = 0
        total_score += max(0, task_score)

        # Task 7: Final Touches (5 pts)
        task_score = 5
        special_char = re.search(r'&[#0-9a-zA-Z]+;', content) is not None
        if not special_char:
            feedback.append("Missing use of a special character entity (e.g., &copy;, &amp;).")
            task_score -= 3
        if len(soup.find_all(style=True)) + (1 if internal_styles else 0) < 3:
            feedback.append("Missing at least 3 additional styles (inline or internal) to enhance the appearance.")
            task_score -= 2
        total_score += max(0, task_score)

        # Overall organization & readability (4 pts)
        task_score = 4
        if not all(tag in content for tag in ['<body>', '<head>', '<html>']):
            feedback.append("Code lacks proper organization and readability.")
            task_score -= 4
        total_score += max(0, task_score)

    except requests.exceptions.RequestException as e:
        feedback.append(f"Failed to fetch website: {e}~~")
        total_score = 0

    return total_score, feedback
