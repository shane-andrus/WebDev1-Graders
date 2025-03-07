import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, scrolledtext
import webbrowser
from tkhtmlview import HTMLLabel

class AutoCanvasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Canvas Grader Viewer")
        self.results_path = self.get_results_path()
        if not self.results_path:
            self.root.destroy()
            return

        self.grading_results_csv = os.path.join(self.results_path, "csv", "grading_results.csv")
        self.fetched_pages_path = os.path.join(self.results_path, "fetched_pages")
        self.grading_results = self.load_grading_results()
        self.selected_file_path = None
        self.assignment_name = "dungeon"
        self.create_widgets()

    def get_results_path(self):
        return filedialog.askdirectory(title="Select Results Folder")

    def load_grading_results(self):
        if os.path.exists(self.grading_results_csv):
            try:
                df = pd.read_csv(self.grading_results_csv, index_col=0)
                results = df.to_dict(orient='index')
                # Parse keys to only include text before the first underscore.
                parsed_results = {key.split('_')[0]: value for key, value in results.items()}
                return parsed_results
            except Exception as e:
                print("Error reading CSV:", e)
        return {}

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame: Listbox of submissions.
        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        tk.Label(left_frame, text="Submissions:").pack(anchor="w")
        # Use takefocus=True so the Listbox can receive keyboard focus.
        self.file_listbox = tk.Listbox(left_frame, width=30, height=25, takefocus=True)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.file_listbox.bind("<<ListboxSelect>>", self.display_html)
        # Bind custom arrow key events.
        self.file_listbox.bind("<KeyPress-Up>", self.handle_arrow)
        self.file_listbox.bind("<KeyPress-Down>", self.handle_arrow)
        # Set initial focus to the listbox.
        self.file_listbox.focus_set()

        # Right frame: Details and HTML preview.
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        tk.Label(right_frame, text="Submission Details:").pack(anchor="w")
        self.text_area = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, height=10)
        self.text_area.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(right_frame, text="HTML Preview:").pack(anchor="w")
        self.html_view = HTMLLabel(right_frame, html="", width=80)
        self.html_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.open_browser_button = tk.Button(self.root, text="Open in Browser", command=self.open_in_browser)
        self.open_browser_button.pack(pady=5)

        self.load_files()

    def load_files(self):
        self.file_listbox.delete(0, tk.END)
        # Create a file name from student name, assignment name, and .html extension.
        for student_name in self.grading_results.keys():
            file_name = f"{student_name}_{self.assignment_name}.html"
            self.file_listbox.insert(tk.END, file_name)
        
        if self.file_listbox.size() > 0:
            self.file_listbox.selection_set(0)
            self.file_listbox.activate(0)
            self.display_html(None)

    def display_html(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        file_name = self.file_listbox.get(selection[0])
        file_path = os.path.join(self.fetched_pages_path, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except Exception as e:
                html_content = f"<p style='color: red;'>Error reading file: {e}</p>"
        else:
            html_content = "<p style='color: red;'>File not found.</p>"

        # Since your grading results use the student name as the key,
        # extract the student name from the file name.
        student_name = file_name.split('_')[0]
        score = self.grading_results.get(student_name, {}).get('Score', 'N/A')
        feedback = self.grading_results.get(student_name, {}).get('Feedback', 'No feedback')
        details_text = f"File: {file_name}\nScore: {score}\nFeedback: {feedback}\n"
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, details_text)
        self.html_view.set_html(html_content)
        self.selected_file_path = file_path if os.path.exists(file_path) else None

    def handle_arrow(self, event):
        """
        Custom arrow key handling to move the selection manually.
        Returning "break" prevents the default behavior, avoiding double movement.
        """
        selection = self.file_listbox.curselection()
        if not selection:
            return "break"
        index = selection[0]
        if event.keysym == "Up" and index > 0:
            new_index = index - 1
        elif event.keysym == "Down" and index < self.file_listbox.size() - 1:
            new_index = index + 1
        else:
            return "break"
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(new_index)
        self.file_listbox.activate(new_index)
        self.display_html(None)
        return "break"  # Prevent default behavior from also moving the selection.

    def open_in_browser(self):
        if self.selected_file_path:
            abs_path = os.path.abspath(self.selected_file_path)
            webbrowser.open(f"file://{abs_path}")
        else:
            self.text_area.insert(tk.END, "\n[Error] Cannot open in browser: File not found.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoCanvasGUI(root)
    root.mainloop()
