import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import List, Tuple
from powercfg_wrapper import list_power_plans, get_active_plan, set_active_plan

class PowerPlanManager:
    def __init__(self, root):
        # Setup basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.root = root
        self.root.title("Windows Power Plan Manager")
        self.root.geometry("600x400")
        self.plans: List[Tuple[str, str, bool]] = []

        # Active plan label
        self.active_label = tk.Label(root, text="Active Plan: Unknown", font=("Arial", 12, "bold"))
        self.active_label.pack(pady=10)

        # Available plans frame
        plans_frame = tk.Frame(root)
        plans_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(plans_frame, text="Available Power Plans:").pack(anchor=tk.W)
        self.plans_listbox = tk.Listbox(plans_frame, height=10)
        self.plans_listbox.pack(pady=5, fill=tk.BOTH, expand=True)

        # Bind single-click to open detail modal
        self.plans_listbox.bind('<Button-1>', self.on_plan_select)

        # Buttons frame
        buttons_frame = tk.Frame(root)
        buttons_frame.pack(pady=10)

        self.set_active_btn = tk.Button(buttons_frame, text="Set Active", command=self.set_active)
        self.set_active_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = tk.Button(buttons_frame, text="Refresh List", command=self.start_refresh_thread)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        # Output text area
        output_frame = tk.Frame(root)
        output_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Label(output_frame, text="Output / Log:").pack(anchor=tk.W)
        self.output_text = tk.Text(output_frame, height=8, wrap=tk.WORD)
        self.output_text.pack(pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.output_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)

        # Initial load
        self.start_refresh_thread()

    def log_output(self, message: str):
        """Append message to output text with timestamp and log to console/file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        self.root.after(0, lambda: self.output_text.insert(tk.END, log_msg + "\n"))
        self.root.after(0, lambda: self.output_text.see(tk.END))
        self.logger.info(message)

    def update_ui_refresh(self, plans_result, active_result):
        """Update UI after refresh thread completes."""
        try:
            plans, plans_output = plans_result
            active_guid, active_output = active_result
            self.plans = plans
            self.plans_listbox.delete(0, tk.END)
            if not plans:
                self.plans_listbox.insert(tk.END, "No power plans available.")
                self.active_label.config(text="Active Plan: None")
                self.log_output("No power plans found.")
                self.logger.warning("No power plans found.")
            else:
                for i, (guid, name, is_active) in enumerate(plans):
                    marker = " (*)" if is_active else ""
                    display = f"{name}{marker}"
                    self.plans_listbox.insert(tk.END, display)
                    if guid == active_guid:
                        self.active_label.config(text=f"Active Plan: {name}")
                self.log_output("Plans refreshed successfully.")
                self.logger.info("Plans refreshed successfully.")
            if plans_output:
                self.log_output(plans_output)
            if active_output:
                self.log_output(active_output)
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error updating UI: {error_msg}")
            if "permission" in error_msg.lower() or "access denied" in error_msg.lower():
                messagebox.showerror("Permission Error", "Insufficient permissions to access power plans. Run as administrator for advanced features.")
            self.log_output(f"Error updating UI: {error_msg}")

    def refresh_plans_thread(self):
        """Thread function for refreshing plans."""
        try:
            plans_result = list_power_plans()
            active_result = get_active_plan()
            self.root.after(0, lambda: self.update_ui_refresh(plans_result, active_result))
        except Exception as e:
            self.root.after(0, lambda: self.log_output(f"Error in refresh thread: {str(e)}"))

    def start_refresh_thread(self):
        """Start thread for refresh."""
        thread = threading.Thread(target=self.refresh_plans_thread, daemon=True)
        thread.start()

    def update_ui_set_active(self, result, guid, name):
        """Update UI after set active thread completes."""
        try:
            stdout, stderr = result
            if stdout:
                self.log_output(f"Successfully set active plan: {name}")
                self.log_output(stdout)
            if stderr:
                self.log_output(f"Warning: {stderr}")
            # Refresh after set
            self.start_refresh_thread()
        except Exception as e:
            error_msg = str(e)
            if "permission" in error_msg.lower() or "access denied" in error_msg.lower():
                messagebox.showerror("Permission Error", f"Insufficient permissions to set '{name}'. Run as administrator.")
            self.log_output(f"Error updating after set: {error_msg}")

    def set_active_thread(self, guid, name):
        """Thread function for setting active plan."""
        try:
            result = set_active_plan(guid)
            self.root.after(0, lambda: self.update_ui_set_active(result, guid, name))
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error in set active thread: {error_msg}")
            self.root.after(0, lambda: self.log_output(f"Error in set active thread: {error_msg}"))

    def on_plan_select(self, event):
        """Handle single-click on a power plan to open detail modal."""
        selection = self.plans_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.plans):
            self.log_output("Invalid selection for details.")
            return
        guid, name, _ = self.plans[index]
        self.open_detail_modal(guid, name)

    def open_detail_modal(self, guid: str, name: str):
        """Open the detail modal for the selected power plan. Placeholder for implementation."""
        # TODO: Implement modal window with details
        self.log_output(f"Opening details for: {name} ({guid})")
        # For now, show a simple message
        messagebox.showinfo("Plan Details", f"Details for {name} (GUID: {guid})\n\nModal implementation pending.")

    def set_active(self):
        """Set the selected plan as active."""
        selection = self.plans_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a power plan.")
            return
        index = selection[0]
        if index >= len(self.plans):
            self.log_output("Invalid selection.")
            self.logger.warning("Invalid selection in set_active.")
            return
        guid, name, _ = self.plans[index]
        # Confirm
        if messagebox.askyesno("Confirm", f"Set '{name}' as active power plan?"):
            self.logger.info(f"Setting active plan: {name} ({guid})")
            thread = threading.Thread(target=self.set_active_thread, args=(guid, name), daemon=True)
            thread.start()
        else:
            self.log_output("Set active cancelled.")
            self.logger.info("Set active cancelled by user.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PowerPlanManager(root)
    root.mainloop()