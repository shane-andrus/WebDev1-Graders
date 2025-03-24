pyinstaller -F -n AssignmentGrader --hidden-import=bs4 --hidden-import=selenium --hidden-import=pandas --hidden-import=pygetwindow --add-data "my_first_website_grader.py;." --add-data "utilities.py;." --add-data "auto_canvas.py;." --add-data "dungeon_grader.py;." --add-data "test_part_2_grader.py;." --add-data "my_first_webpage_grader.py;."
 --add-data "my_second_webpage_grader.py;." --add-binary "chromedriver.exe;." grader_gui.py

 pip install requests beautifulsoup4 selenium pandas pygetwindow pyinstaller urllib3