from __future__ import annotations

import logging
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

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
from browser_automation.interfaces.gui.ui_components import (
    SharedGuiFactory,
    SharedGuiTheme,
)


@dataclass(frozen=True, slots=True)
class GuiConfig(SharedGuiTheme):
    title: str = "Browser Automation Tool"
    width: int = 800
    height: int = 600


class GuiLogHandler(logging.Handler):
    def __init__(self, text_widget):
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
        self.ui = SharedGuiFactory(root, self.config)
        self.use_case = RunAutomationWorkflowUseCase(
            workflow_loader=JsonWorkflowDefinitionLoader(),
            browser_gateway=PlaywrightBrowserAutomationGateway(),
        )
        self._setup_window()
        self._create_widgets()
        self._setup_logging()

    def _setup_window(self):
        self.ui.configure_window(
            self.root,
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            min_width=760,
            min_height=520,
        )

    def _create_widgets(self):
        self.ui.create_header(
            self.root,
            title=self.config.title,
            subtitle="Run a JSON workflow with the same shared desktop UI components used by the Zalo manager.",
            wraplength=720,
        )

        content_frame = self.ui.create_content_frame(self.root)

        # File Selection
        file_frame = self.ui.create_panel(content_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        file_frame.grid_columnconfigure(1, weight=1)

        self.file_path_var = tk.StringVar()
        self.ui.grid_path_row(
            file_frame,
            row=0,
            label="Workflow file",
            variable=self.file_path_var,
            button_text="Browse",
            button_command=self._browse_file,
        )

        # Actions
        btn_frame = tk.Frame(content_frame, bg=self.config.bg_color)
        btn_frame.pack(fill=tk.X, pady=10)

        self.run_btn = self.ui.create_button(
            btn_frame,
            text="Run Workflow",
            command=self._run_workflow_threaded,
            padx=20,
            pady=6,
            variant="primary",
        )
        self.run_btn.pack(side=tk.LEFT)

        # Log Console
        self.ui.create_body_label(
            content_frame,
            "Execution Log",
            bg=self.config.bg_color,
            fg=self.config.text_color,
        ).pack(anchor=tk.W, pady=(10, 5))

        self.log_widget = self.ui.create_scrolled_log(content_frame, height=15)
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
