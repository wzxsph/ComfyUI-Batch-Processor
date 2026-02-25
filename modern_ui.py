import os
import sys
import json
import time
import shutil
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

try:
    from comfy_api import ComfyUIAPI
except ImportError:
    # Fallback if run from a different directory
    from .comfy_api import ComfyUIAPI

class ModernComfyUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ComfyUI Batch Processor Pro")
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.is_running = False
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.preview_queue = queue.Queue()
        
        # Grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_ui()
        self.check_queues()
        
    def setup_ui(self):
        # ------ SIDEBAR (Left) ------
        self.sidebar_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ComfyUI Batch", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Server Config
        self.lbl_server = ctk.CTkLabel(self.sidebar_frame, text="Server Config:")
        self.lbl_server.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.ent_url = ctk.CTkEntry(self.sidebar_frame, placeholder_text="127.0.0.1:8188")
        self.ent_url.insert(0, "127.0.0.1:8188")
        self.ent_url.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        # Paths
        self.lbl_paths = ctk.CTkLabel(self.sidebar_frame, text="Directories & Workflow:")
        self.lbl_paths.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.ent_folder_a = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Input Folder")
        self.ent_folder_a.grid(row=4, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_folder_a = ctk.CTkButton(self.sidebar_frame, text="Select Input", command=lambda: self.select_folder(self.ent_folder_a), fg_color="transparent", border_width=1)
        self.btn_folder_a.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.ent_folder_b = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Output Folder")
        self.ent_folder_b.grid(row=6, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_folder_b = ctk.CTkButton(self.sidebar_frame, text="Select Output", command=lambda: self.select_folder(self.ent_folder_b), fg_color="transparent", border_width=1)
        self.btn_folder_b.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.ent_json = ctk.CTkEntry(self.sidebar_frame, placeholder_text="API JSON File")
        self.ent_json.grid(row=8, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_json = ctk.CTkButton(self.sidebar_frame, text="Select JSON", command=self.select_file, fg_color="transparent", border_width=1)
        self.btn_json.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Node IDs
        self.node_frame = ctk.CTkFrame(self.sidebar_frame, corner_radius=5)
        self.node_frame.grid(row=10, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        self.lbl_load_id = ctk.CTkLabel(self.node_frame, text="LoadImage ID:")
        self.lbl_load_id.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.ent_load_id = ctk.CTkEntry(self.node_frame, width=50)
        self.ent_load_id.insert(0, "202")
        self.ent_load_id.grid(row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="e")
        
        self.lbl_save_id = ctk.CTkLabel(self.node_frame, text="SaveImage ID:")
        self.lbl_save_id.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="w")
        self.ent_save_id = ctk.CTkEntry(self.node_frame, width=50)
        self.ent_save_id.insert(0, "136")
        self.ent_save_id.grid(row=1, column=1, padx=(0, 10), pady=(5, 10), sticky="e")
        
        # Start Button
        self.btn_start = ctk.CTkButton(self.sidebar_frame, text="▶ START BATCH", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_processing)
        self.btn_start.grid(row=11, column=0, padx=20, pady=20, sticky="ew")
        
        # ------ MAIN VIEW (Right) ------
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=3) # Preview gets more space
        self.main_frame.grid_rowconfigure(1, weight=1) # Log gets less space
        
        # Image Preview
        self.preview_lbl = ctk.CTkLabel(self.main_frame, text="Image Preview", bg_color="#2b2b2b", corner_radius=10, font=ctk.CTkFont(size=16))
        self.preview_lbl.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # Console Log
        self.log_area = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=12), state="disabled")
        self.log_area.grid(row=1, column=0, sticky="nsew", pady=(10, 10))
        
        # Progress Bar & Status
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_bar.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Ready", width=100)
        self.lbl_status.pack(side="right")

    def select_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, folder)

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file:
            self.ent_json.delete(0, "end")
            self.ent_json.insert(0, file)

    def append_log(self, message):
        self.log_queue.put(message)

    def update_progress(self, value, maximum):
        self.progress_queue.put((value, maximum))

    def check_queues(self):
        """Polls the queues to update the UI thread-safely."""
        # Process Logs
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_area.configure(state="normal")
            self.log_area.insert("end", msg + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
            self.lbl_status.configure(text=msg.split(":")[-1].strip()[:20] + "...")
            
        # Process Progress
        while not self.progress_queue.empty():
            val, maximum = self.progress_queue.get_nowait()
            if maximum > 0:
                self.progress_bar.set(val / maximum)
                
        # Process Preview
        while not self.preview_queue.empty():
            img_path = self.preview_queue.get_nowait()
            try:
                pil_img = Image.open(img_path)
                # Max scale it down for preview safely
                pil_img.thumbnail((800, 800))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.preview_lbl.configure(text="", image=ctk_img)
            except Exception as e:
                self.append_log(f"⚠️ Failed to load preview: {e}")
                
        self.after(100, self.check_queues)

    def start_processing(self):
        if self.is_running:
            return

        url = self.ent_url.get().strip()
        folder_a = self.ent_folder_a.get().strip()
        folder_b = self.ent_folder_b.get().strip()
        api_json = self.ent_json.get().strip()
        load_id = self.ent_load_id.get().strip()
        save_id = self.ent_save_id.get().strip()

        if not all([url, folder_a, folder_b, api_json, load_id, save_id]):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if not os.path.exists(folder_a) or not os.path.exists(api_json):
            messagebox.showerror("Path Error", "Input folder or API JSON file does not exist.")
            return

        self.is_running = True
        self.btn_start.configure(state="disabled", text="PROCESSING...")
        self.progress_bar.set(0)
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        # Start background thread
        threading.Thread(target=self.process_workflow_thread, args=(url, folder_a, folder_b, api_json, load_id, save_id), daemon=True).start()

    def process_workflow_thread(self, url, folder_a, folder_b, api_json, load_id, save_id):
        try:
            os.makedirs(folder_b, exist_ok=True)
            
            self.append_log("🔄 Initializing ComfyUI API...")
            api = ComfyUIAPI(server_address=url)
            
            if not api.check_connection():
                self.append_log("❌ Failed to connect to ComfyUI. Is it running?")
                self.finish_processing()
                return
                
            with open(api_json, "r", encoding="utf-8") as f:
                workflow_template = json.load(f)

            valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
            images_to_process = [f for f in os.listdir(folder_a) if f.lower().endswith(valid_extensions)]

            if not images_to_process:
                self.append_log(f"📉 No supported images found in {folder_a}.")
                self.finish_processing()
                return

            self.append_log(f"✅ Connected to ComfyUI. Found {len(images_to_process)} images.")

            for i, filename in enumerate(images_to_process, 1):
                self.append_log(f"==============================")
                self.append_log(f"🖼️ [{i}/{len(images_to_process)}] Processing: {filename}")
                self.update_progress(0, 1) # Reset progressive bar
                
                input_filepath = os.path.join(folder_a, filename)
                output_filepath = os.path.join(folder_b, filename)

                # 1. Upload
                self.append_log("📤 Uploading image to ComfyUI...")
                uploaded_name = api.upload_image(input_filepath)

                # 2. Modify Workflow
                workflow = workflow_template.copy()
                if load_id in workflow and "inputs" in workflow[load_id]:
                    workflow[load_id]["inputs"]["image"] = uploaded_name
                if save_id in workflow and "inputs" in workflow[save_id]:
                    workflow[save_id]["inputs"]["filename_prefix"] = "comfy_batch_pro"

                # 3. Process with WebSocket logging
                self.append_log("⚙️ Starting execution pipeline...")
                outputs = api.process_prompt_ws(
                    prompt=workflow,
                    status_callback=lambda val, max_val: self.update_progress(val, max_val),
                    log_callback=lambda msg: self.append_log(msg)
                )

                # 4. Save result
                if outputs and save_id in outputs and "images" in outputs[save_id]:
                    out_info = outputs[save_id]["images"][0]
                    img_data = api.get_image(out_info["filename"], out_info.get("subfolder", ""), out_info.get("type", "output"))
                    
                    with open(output_filepath, "wb") as f:
                        f.write(img_data)
                        
                    self.append_log(f"💾 Saved generated image: {filename}")
                    self.preview_queue.put(output_filepath)
                else:
                    self.append_log(f"⚠️ Warning: Completed but no image outputs found for Node {save_id}.")

            self.append_log("🎉 All images processed successfully!")
            messagebox.showinfo("Done", "Batch processing completed.")

        except Exception as e:
            self.append_log(f"💥 Fatal Error: {str(e)}")
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            
        finally:
            self.finish_processing()

    def finish_processing(self):
        self.is_running = False
        self.btn_start.configure(state="normal", text="▶ START BATCH")
        self.lbl_status.configure(text="Finished")
        self.progress_bar.set(1)

if __name__ == "__main__":
    app = ModernComfyUIApp()
    app.mainloop()
