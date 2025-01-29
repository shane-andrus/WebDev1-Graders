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
    Function to automate grading.

    Args:
    - students: A list of tuples containing (student_name, grade, feedback), 
                where student_name is in the format 'lastnamefirstname' (e.g., 'barkerbob').
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
    speedGrader = input("What is the url of the speed grader you are wanting to interact with?\n")
    driver.get(speedGrader)  # Replace with the URL of your target website

    try:
        # Wait for the login elements to appear
        wait = WebDriverWait(driver, 10)

        # Locate login elements
        window_title = driver.title
        username_input = wait.until(EC.presence_of_element_located((By.ID, "pseudonym_session_unique_id")))
        password_input = wait.until(EC.presence_of_element_located((By.ID, "pseudonym_session_password")))
        login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "Button--login")))

        # Get credentials securely
        username = input("Canvas Username: ")
        password = getpass.getpass("Canvas Password: ")
        updateAll = input("Update All? (y/n): ") == "y"

        # Perform login
        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()

        # Activate the window
        time.sleep(7)
        WebDriverWait(driver, 10).until(lambda d: d.title != window_title)  # Wait for the page title to change
        windows = gw.getWindowsWithTitle(driver.title)
        if windows:
            windows[0].activate()

        while students:
            attempts = 0
            found = False
            student_name_canvas = ""

            while attempts < 3:
                try:
                    # Parse the name from the web
                    student_name_canvas = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ui-selectmenu-item-header"))).text.strip()

                    # Convert the Canvas name to `lastnamefirstname` format
                    canvas_firstname, canvas_lastname = student_name_canvas.split(" ")
                    parsed_name_canvas = f"{canvas_lastname.lower()}{canvas_firstname.lower()}"

                    print(f"Looking for {parsed_name_canvas} in the list.")

                    # Find the tuple in the list of students
                    matching_student = next((student for student in students if student[0] == parsed_name_canvas), None)
                    needs_grading = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-selectmenu-item-icon speedgrader-selectmenu-icon"))).text.strip() == "●"

                    if matching_student and ((needs_grading and not updateAll) or updateAll):
                        raw_name, grade, feedback = matching_student
                        print(f"Setting grade for {student_name_canvas}")

                        # Wait for the grade input to appear
                        grade_input = wait.until(EC.presence_of_element_located((By.ID, "grading-box-extended")))

                        # Enter the grade
                        grade_input.clear()
                        grade_input.send_keys(str(grade))
                        print(f"Grade entered: {grade}")

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
                        time.sleep(5)

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

            # Wait for and click the next button
            next_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "icon-arrow-right")))
            next_button.click()
            time.sleep(5)

    except Exception as e:
        print("Error:", e)

    # Close the browser after interaction
    finally:
        driver.quit()
