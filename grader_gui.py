import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from my_first_website_grader import grade_my_first_website
from utilities import grading_setup, grade_extracted_files
from auto_canvas import putGradesIn
from dungeon_grader import grade_dungeon_map
from test_part_2_grader import grade_html_test_part_2
from my_first_webpage_grader import grade_my_first_webpage
from my_second_webpage_grader import grade_my_second_webpage
import threading

# Grading functions list
grading_functions = [
    ("my first webpage", grade_my_first_webpage),
    ("my second webpage", grade_my_second_webpage),
    ("my first website", grade_my_first_website),
    ("dungeon", grade_dungeon_map),
    ("html test", grade_html_test_part_2),
]

class GradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assignment Grader")
        self.root.geometry("800x600")

        # Variables
        self.uploaded_file_path = tk.StringVar()
        self.results_path = tk.StringVar()
        self.selected_grading_function = tk.StringVar()
        self.canvas_url = tk.StringVar()

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Frame for input fields
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Zip file selection
        ttk.Label(input_frame, text="Zip File Path:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.uploaded_file_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_zip).grid(row=0, column=2, padx=5, pady=5)

        # Results folder selection
        ttk.Label(input_frame, text="Results Folder:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.results_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_results).grid(row=1, column=2, padx=5, pady=5)

        # Grading function selection
        ttk.Label(input_frame, text="Grading Function:").grid(row=2, column=0, padx=5, pady=5)
        grading_options = [name for name, _ in grading_functions]
        self.grading_combo = ttk.Combobox(input_frame, textvariable=self.selected_grading_function, values=grading_options, state="readonly")
        self.grading_combo.grid(row=2, column=1, padx=5, pady=5)
        self.grading_combo.set(grading_options[0])  # Default selection

        # Canvas URL input
        ttk.Label(input_frame, text="Canvas SpeedGrader URL:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.canvas_url, width=50).grid(row=3, column=1, padx=5, pady=5)

        # Run grading button
        ttk.Button(input_frame, text="Run Grading", command=self.start_grading).grid(row=4, column=1, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(input_frame, mode='indeterminate', length=200)
        self.progress.grid(row=5, column=1, pady=5)
        self.progress.grid_remove()  # Hidden by default

        # Results frame
        results_frame = ttk.Frame(self.root, padding="10")
        results_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Treeview for results
        self.tree = ttk.Treeview(results_frame, columns=("Student", "Score", "Feedback"), show="headings", height=15)
        self.tree.heading("Student", text="Student Name")
        self.tree.heading("Score", text="Score")
        self.tree.heading("Feedback", text="Feedback")
        self.tree.column("Student", width=150)
        self.tree.column("Score", width=50)
        self.tree.column("Feedback", width=500)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Submit to Canvas button
        ttk.Button(results_frame, text="Submit to Canvas", command=self.submit_to_canvas).grid(row=1, column=0, pady=10)

        # Make the window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        input_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(0, weight=1)

    def browse_zip(self):
        file_path = filedialog.askopenfilename(filetypes=[("Zip files", "*.zip")])
        if file_path:
            self.uploaded_file_path.set(file_path)

    def browse_results(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.results_path.set(folder_path)

    def start_grading(self):
        uploaded_file = self.uploaded_file_path.get()
        results_folder = self.results_path.get()
        grading_func_name = self.selected_grading_function.get()

        if not uploaded_file or not results_folder:
            messagebox.showerror("Error", "Please select both a zip file and a results folder.")
            return

        if not os.path.exists(uploaded_file):
            messagebox.showerror("Error", "The selected zip file does not exist.")
            return

        # Show progress bar and disable button
        self.progress.grid()
        self.progress.start()
        self.root.children['!frame'].children['!button3'].config(state='disabled')  # Disable "Run Grading" button

        # Run grading in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_grading, args=(uploaded_file, results_folder, grading_func_name), daemon=True).start()

    def run_grading(self, uploaded_file, results_folder, grading_func_name):
        try:
            # Clear previous results
            self.tree.delete(*self.tree.get_children())

            # Setup grading
            extracted_files = grading_setup(uploaded_file, results_folder)

            # Find the selected grading function
            grading_function = next(func for name, func in grading_functions if name == grading_func_name)

            # Grade the files
            grading_tuples = grade_extracted_files(grading_function, results_folder, extracted_files, grading_func_name)

            # Update GUI with results
            self.root.after(0, lambda: self.display_results(grading_tuples))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred during grading: {str(e)}"))
        finally:
            # Hide progress bar and re-enable button
            self.root.after(0, self.stop_progress)

    def display_results(self, grading_tuples):
        for student_name, score, feedback in grading_tuples:
            self.tree.insert("", "end", values=(student_name, score, feedback))
        self.grading_tuples = grading_tuples  # Store for Canvas submission
        messagebox.showinfo("Success", "Grading completed successfully. Results are displayed below.")

    def stop_progress(self):
        self.progress.stop()
        self.progress.grid_remove()
        self.root.children['!frame'].children['!button3'].config(state='normal')  # Re-enable "Run Grading" button

    def submit_to_canvas(self):
        if not hasattr(self, 'grading_tuples') or not self.grading_tuples:
            messagebox.showerror("Error", "No grading results available to submit. Please run grading first.")
            return

        canvas_url = self.canvas_url.get()
        if not canvas_url:
            messagebox.showerror("Error", "Please enter a Canvas SpeedGrader URL.")
            return

        try:
            # Pass the Canvas URL to putGradesIn
            putGradesIn(self.grading_tuples, canvas_url)
            messagebox.showinfo("Success", "Grades submitted to Canvas successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit grades to Canvas: {str(e)}")

def main():
    root = tk.Tk()
    app = GradingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()