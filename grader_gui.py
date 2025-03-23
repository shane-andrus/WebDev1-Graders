import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import webbrowser
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
        self.student_urls = {}

        # Register Chrome explicitly
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Default path, adjust if needed
        if os.path.exists(self.chrome_path):
            webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(self.chrome_path))
        else:
            self.chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"  # Alternative path
            if os.path.exists(self.chrome_path):
                webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(self.chrome_path))

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
        self.grading_combo.set(grading_options[0])

        # Canvas URL input
        ttk.Label(input_frame, text="Canvas SpeedGrader URL:").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.canvas_url, width=50).grid(row=3, column=1, padx=5, pady=5)

        # Run grading button
        ttk.Button(input_frame, text="Run Grading", command=self.start_grading).grid(row=4, column=1, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(input_frame, mode='indeterminate', length=200)
        self.progress.grid(row=5, column=1, pady=5)
        self.progress.grid_remove()

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

        # Context menu for right-click
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View URL in Chrome", command=self.view_url_in_chrome)
        self.tree.bind("<Button-3>", self.show_context_menu)

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

        self.progress.grid()
        self.progress.start()
        self.root.children['!frame'].children['!button3'].config(state='disabled')
        threading.Thread(target=self.run_grading, args=(uploaded_file, results_folder, grading_func_name), daemon=True).start()

    def run_grading(self, uploaded_file, results_folder, grading_func_name):
        try:
            self.tree.delete(*self.tree.get_children())
            extracted_files = grading_setup(uploaded_file, results_folder)
            grading_function = next(func for name, func in grading_functions if name == grading_func_name)
            grading_tuples = self.grade_extracted_files_with_urls(grading_function, results_folder, extracted_files, grading_func_name)
            self.root.after(0, lambda: self.display_results(grading_tuples))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred during grading: {str(e)}"))
        finally:
            self.root.after(0, self.stop_progress)

    def grade_extracted_files_with_urls(self, grading_function, results_path, extracted_files, assignment_name):
        grading_tuples = []
        pulled_path = os.path.join(results_path, "pulled_html")
        for file_name in extracted_files:
            file_path = os.path.join(pulled_path, file_name)
            if os.path.isdir(file_path):
                continue

            try:
                url = extract_url_from_html(file_path)
                student_name = file_name.split('_')[0]
                if not url or "localhost" in url or "127.0.0.1" in url:
                    feedback = "Invalid or local URL submitted."
                    score = 1
                else:
                    score, feedback = grading_function(url, student_name, assignment_name)
                    feedback = "; ".join(feedback) if feedback else "Good job!"
                    self.student_urls[student_name] = url
                grading_tuples.append((student_name, score, feedback))
            except Exception as e:
                grading_tuples.append((student_name, 1, f"Error processing: {str(e)}"))
        return grading_tuples

    def display_results(self, grading_tuples):
        for student_name, score, feedback in grading_tuples:
            self.tree.insert("", "end", values=(student_name, score, feedback))
        self.grading_tuples = grading_tuples
        messagebox.showinfo("Success", "Grading completed successfully. Results are displayed below.")

    def stop_progress(self):
        self.progress.stop()
        self.progress.grid_remove()
        self.root.children['!frame'].children['!button3'].config(state='normal')

    def submit_to_canvas(self):
        if not hasattr(self, 'grading_tuples') or not self.grading_tuples:
            messagebox.showerror("Error", "No grading results available to submit. Please run grading first.")
            return

        canvas_url = self.canvas_url.get()
        if not canvas_url:
            messagebox.showerror("Error", "Please enter a Canvas SpeedGrader URL.")
            return

        try:
            putGradesIn(self.grading_tuples, canvas_url)
            messagebox.showinfo("Success", "Grades submitted to Canvas successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit grades to Canvas: {str(e)}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def view_url_in_chrome(self):
        selected_item = self.tree.selection()
        if selected_item:
            student_name = self.tree.item(selected_item, "values")[0]
            url = self.student_urls.get(student_name)
            if url:
                try:
                    if 'chrome' in webbrowser._browsers:  # Check if Chrome is registered
                        webbrowser.get('chrome').open(url)
                    else:
                        # Fallback to default browser if Chrome isn’t available
                        webbrowser.open(url)
                        messagebox.showwarning("Browser Issue", "Chrome not found. Opening in default browser.")
                except webbrowser.Error:
                    messagebox.showerror("Error", "Could not open Chrome. Ensure it’s installed or check the path.")
            else:
                messagebox.showinfo("No URL", f"No valid URL found for {student_name}.")

def extract_url_from_html(file_path):
    from bs4 import BeautifulSoup
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'Refresh'})
    if meta_refresh:
        return meta_refresh.get('content').split('url=')[-1].strip()
    anchor_tag = soup.find('a', href=True)
    return anchor_tag['href'] if anchor_tag else None

def main():
    root = tk.Tk()
    app = GradingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()