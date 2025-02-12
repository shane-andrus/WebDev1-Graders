from my_first_website_grader import grade_my_first_website
from utilities import grading_setup, grade_extracted_files
from auto_canvas import putGradesIn
from dungeon_grader import grade_dungeon_map
from test_part_2_grader import grade_html_test_part_2
from my_first_webpage_grader import grade_my_first_webpage
from my_second_webpage_grader import grade_my_second_webpage

grading_functions = [
    ("my first webpage", grade_my_first_webpage),
    ("my second webpage", grade_my_second_webpage),
    ("my first website", grade_my_first_website),
    ("dungeon", grade_dungeon_map),
    ("html test", grade_html_test_part_2),
]

def main():
    # Input paths
    uploaded_file_path = input("Path to the uploaded zip file containing submissions: ")
    results_path = input("Path to save grading results: ")

    # Ensure the grading setup is ready
    extracted_files = grading_setup(uploaded_file_path, results_path)

    # Display grading function options
    print("Available grading functions:")
    for idx, (name, _) in enumerate(grading_functions, start=1):
        print(f"{idx}. {name}")

    # Prompt user to select a grading function
    try:
        selection = int(input("Enter the number of the grading function to use: "))
        if selection < 1 or selection > len(grading_functions):
            raise ValueError("Invalid selection.")
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Get the selected grading function
    grading_function = grading_functions[selection - 1][1]

    # Grade the extracted files
    grading_tuples = grade_extracted_files(grading_function, results_path, extracted_files, grading_functions[selection - 1][0])

    # Submit grades to Canvas
    putGradesIn(grading_tuples)

    print("Grading complete. Results submitted to Canvas.")

if __name__ == "__main__":
    main()