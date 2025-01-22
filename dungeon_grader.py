from bs4 import BeautifulSoup
import requests

# Function to grade a dungeon map URL
def grade_dungeon_map(url, student_name, assignment_name):
    feedback = []
    total_score = 40  # Starting from full score

    try:
        # Fetch the website HTML with SSL verification disabled
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.text

        soup = BeautifulSoup(content, 'html.parser')

        # 1. Check for the 1st table (25 pts)
        first_table = soup.find('table')
        if first_table:
            rows = first_table.find_all('tr')
            if len(rows) >= 5 and all(len(row.find_all(['td', 'th'])) >= 5 for row in rows[:5]):
                # Check for an image inside the table
                image = first_table.find('img')
                if not image:
                    feedback.append("First table is missing an image~~")
                    total_score -= 5

                # Check for at least 1 external link
                link = first_table.find('a', href=True)
                if not link or "http" not in link['href']:
                    feedback.append("First table is missing an external link~~")
                    total_score -= 5

                # Check for background colors, font colors, or other styles
                styles = first_table.get('style') or any(cell.get('style') for cell in first_table.find_all(['td', 'th']))
                if not styles:
                    feedback.append("First table is missing background or font styles~~")
                    total_score -= 5
            else:
                feedback.append("First table does not have at least 5 rows and 5 columns~~")
                total_score -= 10
        else:
            feedback.append("Missing the first table for the dungeon map~~")
            total_score -= 25

        # 2. Check for the 2nd table (10 pts)
        second_table = soup.find_all('table')[1] if len(soup.find_all('table')) > 1 else None
        if second_table:
            rows = second_table.find_all('tr')
            if len(rows) >= 6 and all(len(row.find_all(['td', 'th'])) >= 2 for row in rows):
                # Check if the top row is styled as a header
                header = rows[0].find_all('th')
                if not header:
                    feedback.append("Second table is missing a styled header row~~")
                    total_score -= 5
            else:
                feedback.append("Second table does not have at least 6 rows and 2 columns~~")
                total_score -= 5
        else:
            feedback.append("Missing the second table for the key/legend~~")
            total_score -= 10

        # 3. Check for headings (5 pts)
        headings = soup.find_all(['h1', 'h2', 'h3'])
        second_table_heading = any(heading.find_next('table') == second_table for heading in headings) if second_table else False

        if not second_table_heading:
            feedback.append("Ensure the second table has a corresponding heading before it. ~~")
            total_score -= 5

    except requests.exceptions.RequestException as e:
        feedback.append(f"Failed to fetch website: {e}~~")
        total_score = 0

    return total_score, feedback
