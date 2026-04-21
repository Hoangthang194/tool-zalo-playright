from __future__ import annotations

import logging
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from browser_automation.application.use_cases.run_workflow import (
    RunAutomationWorkflowUseCase,
)
from browser_automation.domain.exceptions import (
    BrowserAutomationError,
    WorkflowValidationError,
)
from browser_automation.infrastructure.playwright_adapter.playwright_browser_gateway import (
    PlaywrightBrowserAutomationGateway,
)
from browser_automation.infrastructure.workflow_loader import JsonWorkflowDefinitionLoader

@dataclass
class GuiConfig:
    title: str = "Browser Automation Tool"
    width: int = 800
    height: int = 600
    primary_color: str = "#2c3e50"
    secondary_color: str = "#34495e"
    accent_color: str = "#3498db"
    text_color: str = "#ecf0f1"


class GuiLogHandler(logging.Handler):
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)


class AutomationGui:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = GuiConfig()
        self.use_case = RunAutomationWorkflowUseCase(
            workflow_loader=JsonWorkflowDefinitionLoader(),
            browser_gateway=PlaywrightBrowserAutomationGateway(),
        )
        self._setup_window()
        self._create_widgets()
        self._setup_logging()

    def _setup_window(self):
        self.root.title(self.config.title)
        self.root.geometry(f"{self.config.width}x{self.config.height}")
        self.root.configure(bg=self.config.primary_color)

    def _create_widgets(self):
        # Main Layout
        padding = 20
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.config.secondary_color, padx=padding, pady=padding)
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame, 
            text=self.config.title, 
            font=("Helvetica", 18, "bold"),
            bg=self.config.secondary_color,
            fg=self.config.accent_color
        ).pack(side=tk.LEFT)

        # Content
        content_frame = tk.Frame(self.root, bg=self.config.primary_color, padx=padding, pady=padding)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # File Selection
        file_frame = tk.Frame(content_frame, bg=self.config.primary_color)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            file_frame, 
            text="Workflow File:", 
            bg=self.config.primary_color, 
            fg=self.config.text_color
        ).pack(side=tk.LEFT)

        self.file_path_var = tk.StringVar()
        entry = tk.Entry(
            file_frame, 
            textvariable=self.file_path_var, 
            width=50,
            bg=self.config.secondary_color,
            fg=self.config.text_color,
            insertbackground=self.config.text_color,
            border=0
        )
        entry.pack(side=tk.LEFT, padx=10)

        tk.Button(
            file_frame, 
            text="Browse", 
            command=self._browse_file,
            bg=self.config.accent_color,
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.LEFT)

        # Actions
        btn_frame = tk.Frame(content_frame, bg=self.config.primary_color)
        btn_frame.pack(fill=tk.X, pady=10)

        self.run_btn = tk.Button(
            btn_frame, 
            text="Run Workflow", 
            command=self._run_workflow_threaded,
            bg="#27ae60",
            fg="white",
            activebackground="#2ecc71",
            activeforeground="white",
            relief=tk.FLAT,
            font=("Helvetica", 10, "bold"),
            padx=20,
            pady=5
        )
        self.run_btn.pack(side=tk.LEFT)

        # Log Console
        tk.Label(
            content_frame, 
            text="Execution Log:", 
            bg=self.config.primary_color, 
            fg=self.config.text_color
        ).pack(anchor=tk.W, pady=(10, 5))

        self.log_widget = scrolledtext.ScrolledText(
            content_frame, 
            height=15, 
            bg="#1a252f", 
            fg="#95a5a6",
            font=("Consolas", 10),
            state='disabled',
            border=0
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)

    def _setup_logging(self):
        logger = logging.getLogger("browser_automation")
        logger.setLevel(logging.INFO)
        handler = GuiLogHandler(self.log_widget)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also redirect root logger if necessary
        # logging.getLogger().addHandler(handler)

    def _browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Workflow JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)

    def _run_workflow_threaded(self):
        path_str = self.file_path_var.get()
        if not path_str:
            messagebox.showwarning("Warning", "Please select a workflow file first.")
            return

        self.run_btn.configure(state='disabled', text="Running...")
        self.log_widget.configure(state='normal')
        self.log_widget.delete(1.0, tk.END)
        self.log_widget.configure(state='disabled')
        
        thread = threading.Thread(target=self._run_workflow, args=(Path(path_str),), daemon=True)
        thread.start()

    def _run_workflow(self, path: Path):
        try:
            result = self.use_case.execute(path)
            logging.getLogger("browser_automation").info(
                f"Successfully completed: {result.workflow_name} ({result.steps_executed} steps)"
            )
        except (BrowserAutomationError, WorkflowValidationError, FileNotFoundError, OSError) as exc:
            logging.getLogger("browser_automation").error(f"Error: {exc}")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state='normal', text="Run Workflow"))


def main():
    root = tk.Tk()
    app = AutomationGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
