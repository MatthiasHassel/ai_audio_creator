import os
import threading
import json
import hashlib
from tkinter import filedialog
from services.pdf_analysis_service import PDFAnalysisService

class ScriptEditorController:
    def __init__(self, model, view, config, project_model):
        self.model = model
        self.view = view
        self.config = config
        self.project_model = project_model
        self.current_script_path = None
        self.pdf_analysis_service = PDFAnalysisService(config)
        self.setup_view_commands()

    def setup_view_commands(self):
        self.view.save_button.configure(command=self.save_script)
        self.view.load_button.configure(command=self.load_script)
        self.view.set_import_pdf_callback(self.import_pdf)
        self.view.set_analyze_script_callback(self.analyze_script)


    def format_text(self, style):
        self.view.format_text(style)

    def get_script_hash(self):
        return hashlib.md5(self.get_script_text().encode()).hexdigest()

    def is_script_modified(self):
        return self.last_saved_hash != self.get_script_hash()

    def save_script(self):
        if not self.project_model.current_project:
            self.view.update_status("No active project. Please open or create a project first.")
            return

        initial_dir = self.project_model.get_scripts_dir()
        initial_file = os.path.basename(self.current_script_path) if self.current_script_path else ""
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.get_script_text())
            self.current_script_path = file_path
            relative_path = os.path.relpath(file_path, self.project_model.get_scripts_dir())
            self.project_model.set_last_opened_script(relative_path)
            self.view.update_status(f"Script saved to {file_path}")

    def load_script(self, file_path=None):
        if not self.project_model.current_project:
            self.view.update_status("No active project. Please open or create a project first.")
            return

        if not file_path:
            file_path = filedialog.askopenfilename(
                initialdir=self.project_model.get_scripts_dir(),
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    script_content = file.read()
                self.set_script_text(script_content)
                self.current_script_path = file_path
                relative_path = os.path.relpath(file_path, self.project_model.get_scripts_dir())
                self.project_model.set_last_opened_script(relative_path)
                self.view.update_status(f"Script loaded from {file_path}")
            except Exception as e:
                error_message = f"Error loading script: {str(e)}"
                self.view.update_status(error_message)
                self.view.show_error("Error", error_message)

    def get_script_text(self):
        return self.view.get_text()

    def set_script_text(self, text):
        self.model.set_content(text)
        self.view.set_text(text)

    def clear_text(self):
        self.set_script_text("")
        self.current_script_path = None

    def update_scripts_directory(self, directory):
        # This method might not be necessary anymore, but keep it for potential future use
        pass

    def import_pdf(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            try:
                text = self.pdf_analysis_service.extract_text_from_pdf(file_path)
                self.view.set_text(text)
                self.view.update_status(f"PDF imported: {file_path}")
            except Exception as e:
                self.view.update_status(f"Error importing PDF: {str(e)}")

    def analyze_script(self):
        script_text = self.view.get_text()
        if not script_text:
            self.view.update_status("Error: No script text to analyze")
            return

        self.view.show_progress_bar(determinate=False)  # Use indeterminate mode
        self.view.analyze_script_button.configure(state="disabled")

        def analysis_thread():
            try:
                analysis = self.pdf_analysis_service.analyze_script(script_text)
                if analysis:
                    output_path = self.get_next_analysis_filename()
                    with open(output_path, 'w') as file:
                        json.dump(analysis, file, indent=2)
                    self.view.after(0, lambda: self.view.update_status(f"Analysis saved to: {output_path}"))
                else:
                    self.view.after(0, lambda: self.view.update_status("Error: Failed to analyze script"))
            except Exception as e:
                self.view.after(0, lambda: self.view.update_status(f"Error analyzing script: {str(e)}"))
            finally:
                self.view.after(0, self.view.hide_progress_bar)
                self.view.after(0, lambda: self.view.analyze_script_button.configure(state="normal"))

        threading.Thread(target=analysis_thread, daemon=True).start()

    def get_next_analysis_filename(self):
        scripts_dir = self.project_model.get_scripts_dir()
        index = 1
        while True:
            filename = f"script_analysis{index}.json"
            full_path = os.path.join(scripts_dir, filename)
            if not os.path.exists(full_path):
                return full_path
            index += 1