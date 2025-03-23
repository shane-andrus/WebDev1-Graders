from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pygetwindow as gw
import getpass
import time

def putGradesIn(students):
    """
    Function to automate grading in Canvas SpeedGrader.

    Args:
    - students: A list of tuples containing (student_name, grade, feedback), 
                where student_name is in the format 'middlename1middlename2lastnamefirstname'.
    """
    print()
    # Set logging preferences in DesiredCapabilities
    caps = DesiredCapabilities.CHROME.copy()
    caps['goog:loggingPrefs'] = {'browser': 'OFF', 'driver': 'OFF'}

    # Configure ChromeOptions
    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'browser': 'OFF', 'driver': 'OFF'})

    # Initialize WebDriver
    driver = webdriver.Chrome(options=options)
    speedGrader = input("What is the URL of the SpeedGrader you want to interact with?\n")
    driver.get(speedGrader)  # Open the SpeedGrader page

    try:
        # Wait for the login elements to appear
        wait = WebDriverWait(driver, 10)

        # Locate login elements
        username_input = wait.until(EC.presence_of_element_located((By.ID, "pseudonym_session_unique_id")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "pseudonym_session_password")))
        login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "Button--login")))

        # Get credentials securely
        username = input("Canvas Username: ")
        password = getpass.getpass("Canvas Password: ")
        updateAll = input("Update All? (y/n): ").strip().lower() == "y"

        # Perform login
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()

        # Allow time for the page to load
        time.sleep(4)

        while students:
            attempts = 0
            found = False
            student_name_canvas = ""
            parsed_name_canvas = ""  # Ensure it's always initialized
            needs_grading = True

            while attempts < 3 and needs_grading:
                try:
                    # Parse the name from the web
                    student_name_canvas = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ui-selectmenu-item-header"))).text.strip()

                    # Check if the student needs grading
                    needs_grading = len(driver.find_elements(By.CLASS_NAME, "ui-selectmenu-item-icon.speedgrader-selectmenu-icon")) >= 1
                    if not needs_grading and not updateAll:
                        break

                    # Handle names dynamically, including multiple middle names
                    name_parts = student_name_canvas.split(" ")
                    print(f"Raw name: {student_name_canvas}, Split parts: {name_parts}")

                    if len(name_parts) >= 2:
                        canvas_firstname = name_parts[0]
                        canvas_lastname = name_parts[-1].replace("-", "")  # Remove hyphens in last names
                        canvas_middlenames = "".join(name_parts[1:-1])  # Combine all middle parts
                        parsed_name_canvas = f"{canvas_middlenames.lower()}{canvas_lastname.lower()}{canvas_firstname.lower()}"
                    else:
                        raise ValueError(f"Invalid name format: {student_name_canvas}")

                    print(f"Looking for {parsed_name_canvas} in the list.")

                    # Find the tuple in the list of students
                    matching_student = next((student for student in students if student[0] == parsed_name_canvas), None)

                    if matching_student:
                        raw_name, grade, feedback = matching_student
                        print(f"Setting grade for {student_name_canvas}")

                        # Wait for the grade input to appear
                        grade_input = wait.until(EC.presence_of_element_located((By.ID, "grading-box-extended")))
                        current_grade = grade_input.get_attribute("value").strip()

                        # Only update if the grade is different
                        if current_grade == "" or current_grade != str(grade):
                            grade_input.clear()
                            grade_input.send_keys(str(grade))
                            print(f"Grade updated: {grade}")

                            # Locate and switch to the iframe for feedback
                            iframe = wait.until(EC.presence_of_element_located((By.ID, "comment_rce_textarea_ifr")))
                            driver.switch_to.frame(iframe)

                            # Locate the feedback area
                            feedback_area = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))

                            # Enter feedback
                            feedback_area.clear()
                            feedback_area.send_keys(feedback)
                            print(f"Feedback entered: {feedback}")

                            # Switch back to the main content
                            driver.switch_to.default_content()

                            feedback_submit = driver.find_element(By.ID, "comment_submit_button")
                            time.sleep(1)
                            feedback_submit.click()
                            time.sleep(3)

                        else:
                            print(f"Grade already set to {current_grade}, no update needed.")

                        # Remove the successfully submitted student from the list
                        students.remove(matching_student)
                        print(f"Successfully submitted for {parsed_name_canvas}. Removed from the list.")
                        found = True
                        break

                except Exception as e:
                    print(f"Error during attempt {attempts + 1}: {e}")

                attempts += 1

            if not found:
                print(f"Student {student_name_canvas} not found after 3 attempts. Removing from the list and skipping...")
                if student_name_canvas:
                    students = [student for student in students if student[0] != parsed_name_canvas]
            print(f"{len(students)} Students Remaining")

            # Wait for and click the next button
            try:
                next_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "icon-arrow-right")))
                next_button.click()
                time.sleep(3)
            except Exception:
                print("No next button found. Ending grading process.")
                break

    except Exception as e:
        print("Error:", e)

    finally:
        # Close the browser after interaction
        driver.quit()
