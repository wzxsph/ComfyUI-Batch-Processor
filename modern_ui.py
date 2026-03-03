import os
import json
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

try:
    from comfy_api import ComfyUIAPI
except ImportError:
    from .comfy_api import ComfyUIAPI

from localization import get_localizer, t

class ABComparisonWidget(ctk.CTkFrame):
    """
    A custom widget that displays an interactive A/B slider for comparing two images.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.split_pct = 0.5
        self.img_a_pil = None
        self.img_b_pil = None
        
        self.canvas = tk.Canvas(self, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-1>", self.on_drag)
        
        self._photo_a = None
        self._photo_b = None
        self._canvas_width = 1
        self._canvas_height = 1
        self._draw_pending = False

    def set_images(self, path_a, path_b):
        """Loads the images into memory and refreshes the canvas."""
        try:
            if path_a and os.path.exists(path_a):
                self.img_a_pil = Image.open(path_a).convert("RGB")
            else:
                self.img_a_pil = None
                
            if path_b and os.path.exists(path_b):
                self.img_b_pil = Image.open(path_b).convert("RGB")
            else:
                self.img_b_pil = None
        except Exception as e:
            print(f"Error loading images: {e}")
            self.img_a_pil = None
            self.img_b_pil = None
            
        self.schedule_draw()

    def on_resize(self, event):
        if event.width > 10 and event.height > 10:
            self._canvas_width = event.width
            self._canvas_height = event.height
            self.schedule_draw()

    def on_drag(self, event):
        if self._canvas_width > 0:
            self.split_pct = max(0.0, min(1.0, event.x / self._canvas_width))
            self.schedule_draw()

    def schedule_draw(self):
        if not self._draw_pending:
            self._draw_pending = True
            self.after(15, self.draw)

    def draw(self):
        """Redraws the canvas with dynamically resized images."""
        self._draw_pending = False
        self.canvas.delete("all")
        
        if not self.img_a_pil and not self.img_b_pil:
            self.canvas.create_text(self._canvas_width/2, self._canvas_height/2, text=t('canvas_no_images'), fill="#aaaaaa", justify="center", font=("Arial", 16))
            return

        ref_img = self.img_b_pil if self.img_b_pil else self.img_a_pil
        if not ref_img:
            return
        
        img_w, img_h = ref_img.size
        ratio = min(self._canvas_width / img_w, self._canvas_height / img_h)
        new_w = max(1, int(img_w * ratio))
        new_h = max(1, int(img_h * ratio))
        
        off_x = (self._canvas_width - new_w) // 2
        off_y = (self._canvas_height - new_h) // 2
        
        split_x_in_img = int(new_w * self.split_pct)
        
        # Left Side (Image A - Original)
        if self.img_a_pil and split_x_in_img > 0:
            img_a_resized = self.img_a_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img_a_crop = img_a_resized.crop((0, 0, split_x_in_img, new_h))
            self._photo_a = ImageTk.PhotoImage(img_a_crop)
            self.canvas.create_image(off_x, off_y, anchor="nw", image=self._photo_a)
            
        # Right Side (Image B - Generated)
        if self.img_b_pil and split_x_in_img < new_w:
            img_b_resized = self.img_b_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img_b_crop = img_b_resized.crop((split_x_in_img, 0, new_w, new_h))
            self._photo_b = ImageTk.PhotoImage(img_b_crop)
            self.canvas.create_image(off_x + split_x_in_img, off_y, anchor="nw", image=self._photo_b)
            
        # Delimiter Line & Handle
        if self.img_a_pil and self.img_b_pil:
            line_x = off_x + split_x_in_img
            self.canvas.create_line(line_x, off_y, line_x, off_y + new_h, fill="white", width=2)
            self.canvas.create_oval(line_x - 5, off_y + new_h//2 - 5, line_x + 5, off_y + new_h//2 + 5, fill="white", outline="#cccccc")
        
        # Labels
        if self.img_a_pil:
            self.canvas.create_text(off_x + 10, off_y + 10, text=t('label_original'), fill="white", anchor="nw", font=("Arial", 14, "bold"))
        if self.img_b_pil:
            self.canvas.create_text(off_x + new_w - 10, off_y + 10, text=t('label_generated'), fill="white", anchor="ne", font=("Arial", 14, "bold"))


class ModernComfyUIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.localizer = get_localizer()
        self.title(t('app_title'))
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.is_running = False
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.gallery_sync_queue = queue.Queue()
        
        self.gallery_images = []
        self.current_gallery_idx = -1
        self.console_visible = True
        
        # Grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_ui()
        self.check_queues()
        self.load_gallery_from_disk()
    
    def change_language(self, lang_code):
        """Change the language and reload UI."""
        if self.localizer.set_language(lang_code):
            # Restart the application by destroying and recreating
            self.destroy()
            app = ModernComfyUIApp()
            app.mainloop()
        
    def setup_ui(self):
        # ------ SIDEBAR (Left) ------
        self.sidebar_frame = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)
        
        # Language Selector (Top)
        lang_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        lbl_lang = ctk.CTkLabel(lang_frame, text=t('language_selector_label'), font=ctk.CTkFont(family="Microsoft YaHei", size=11))
        lbl_lang.pack(side="left")
        
        lang_options = [self.localizer.get_language_name('en'), self.localizer.get_language_name('zh')]
        current_lang_name = self.localizer.get_language_name()
        
        self.lang_combobox = ctk.CTkComboBox(
            lang_frame,
            values=lang_options,
            state="readonly",
            width=100,
            font=ctk.CTkFont(family="Microsoft YaHei", size=11),
            command=self._on_language_change
        )
        self.lang_combobox.set(current_lang_name)
        self.lang_combobox.pack(side="right")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=t('logo_text'), font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold"))
        self.logo_label.grid(row=1, column=0, padx=20, pady=(20, 10))
        
        # Server Config
        self.lbl_server = ctk.CTkLabel(self.sidebar_frame, text=t('server_config'), font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.lbl_server.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.ent_url = ctk.CTkEntry(self.sidebar_frame, placeholder_text=t('server_placeholder'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.ent_url.insert(0, "127.0.0.1:8188")
        self.ent_url.grid(row=3, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        # Paths
        self.lbl_paths = ctk.CTkLabel(self.sidebar_frame, text=t('directories_workflow'), font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.lbl_paths.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.ent_folder_a = ctk.CTkEntry(self.sidebar_frame, placeholder_text=t('input_folder_placeholder'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.ent_folder_a.grid(row=5, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_folder_a = ctk.CTkButton(self.sidebar_frame, text=t('btn_select_input'), command=lambda: self.select_folder(self.ent_folder_a), fg_color="transparent", border_width=1, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.btn_folder_a.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.ent_folder_b = ctk.CTkEntry(self.sidebar_frame, placeholder_text=t('output_folder_placeholder'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.ent_folder_b.grid(row=7, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_folder_b = ctk.CTkButton(self.sidebar_frame, text=t('btn_select_output'), command=lambda: self.select_folder(self.ent_folder_b), fg_color="transparent", border_width=1, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.btn_folder_b.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.ent_json = ctk.CTkEntry(self.sidebar_frame, placeholder_text=t('api_json_placeholder'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.ent_json.grid(row=9, column=0, padx=20, pady=(5, 5), sticky="ew")
        self.btn_json = ctk.CTkButton(self.sidebar_frame, text=t('btn_select_json'), command=self.select_file, fg_color="transparent", border_width=1, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.btn_json.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Node IDs
        self.node_frame = ctk.CTkFrame(self.sidebar_frame, corner_radius=5)
        self.node_frame.grid(row=11, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        self.lbl_load_id = ctk.CTkLabel(self.node_frame, text=t('load_image_id'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.lbl_load_id.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.ent_load_id = ctk.CTkEntry(self.node_frame, width=50)
        self.ent_load_id.insert(0, "202")
        self.ent_load_id.grid(row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="e")
        
        self.lbl_save_id = ctk.CTkLabel(self.node_frame, text=t('save_image_id'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.lbl_save_id.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="w")
        self.ent_save_id = ctk.CTkEntry(self.node_frame, width=50)
        self.ent_save_id.insert(0, "136")
        self.ent_save_id.grid(row=1, column=1, padx=(0, 10), pady=(5, 10), sticky="e")
        
        # Output Prefix
        self.lbl_prefix = ctk.CTkLabel(self.sidebar_frame, text=t('output_prefix_label'), font=ctk.CTkFont(family="Microsoft YaHei", size=14))
        self.lbl_prefix.grid(row=12, column=0, padx=20, pady=(5, 0), sticky="w")
        self.ent_prefix = ctk.CTkEntry(self.sidebar_frame, placeholder_text=t('output_prefix_placeholder'), font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.ent_prefix.grid(row=13, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        # Start Button
        self.btn_start = ctk.CTkButton(self.sidebar_frame, text=t('btn_start'), height=50, font=ctk.CTkFont(family="Microsoft YaHei", weight="bold", size=18), command=self.start_processing)
        self.btn_start.grid(row=14, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # ------ MAIN VIEW (Right) ------
        # Main Frame configuration for full responsiveness
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1) # Preview Canvas takes max space
        self.main_frame.grid_rowconfigure(3, weight=0) # Log Area takes strict space when visible
        
        # 1. Image Preview & Gallery Zone
        self.preview_container = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.preview_container.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.preview_container.grid_columnconfigure(0, weight=1)
        self.preview_container.grid_rowconfigure(0, weight=1)
        
        self.ab_widget = ABComparisonWidget(self.preview_container)
        self.ab_widget.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # 2. Gallery Navigation
        self.gallery_frame = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        self.gallery_frame.grid(row=1, column=0, sticky="ew", pady=(5, 10))
        self.gallery_frame.grid_columnconfigure(1, weight=1) # Center label expands
        
        self.btn_prev = ctk.CTkButton(self.gallery_frame, text=t('btn_prev'), width=90, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=14), command=self.prev_image)
        self.btn_prev.grid(row=0, column=0, padx=10)
        
        self.lbl_gallery_status = ctk.CTkLabel(self.gallery_frame, text=t('gallery_status', count=0), font=ctk.CTkFont(family="Microsoft YaHei", size=14, weight="bold"))
        self.lbl_gallery_status.grid(row=0, column=1)
        
        self.btn_reload = ctk.CTkButton(self.gallery_frame, text=t('btn_refresh'), width=70, height=32, fg_color="transparent", border_width=1, font=ctk.CTkFont(family="Microsoft YaHei", size=13), command=self.load_gallery_from_disk)
        self.btn_reload.grid(row=0, column=2, padx=(0, 10))
        
        self.btn_next = ctk.CTkButton(self.gallery_frame, text=t('btn_next'), width=90, height=32, font=ctk.CTkFont(family="Microsoft YaHei", size=14), command=self.next_image)
        self.btn_next.grid(row=0, column=3, padx=10)

        # 3. Console Toggle
        self.btn_toggle_console = ctk.CTkButton(self.main_frame, text=t('btn_hide_console'), width=130, height=30, fg_color="#333", hover_color="#444", font=ctk.CTkFont(family="Microsoft YaHei", size=13), command=self.toggle_console)
        self.btn_toggle_console.grid(row=1, column=0, sticky="w", pady=(5, 5))
        
        # 4. Console Log Area
        self.log_area = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=13), state="disabled", height=120)
        self.log_area.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        
        # 5. Progress Bar & Status
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, sticky="ew")
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_bar.set(0)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text=t('status_ready'), width=100, font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.lbl_status.pack(side="right")

    # --- UI Logic Methods ---
    def _on_language_change(self, choice):
        """Handle language selection change."""
        lang_code = 'en' if choice == self.localizer.get_language_name('en') else 'zh'
        self.change_language(lang_code)
    
    def select_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, folder)
            self.load_gallery_from_disk()

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[(t('file_dialog_json'), "*.json")])
        if file:
            self.ent_json.delete(0, "end")
            self.ent_json.insert(0, file)

    def toggle_console(self):
        """Hides or shows the console to free up space for the image preview."""
        self.console_visible = not self.console_visible
        if self.console_visible:
            self.log_area.grid()
            self.btn_toggle_console.configure(text=t('btn_hide_console'))
        else:
            self.log_area.grid_remove()
            self.btn_toggle_console.configure(text=t('btn_show_console'))

    def load_gallery_from_disk(self):
        folder_b = self.ent_folder_b.get().strip()
        if not folder_b or not os.path.exists(folder_b):
            self.gallery_images = []
            self.update_gallery_view()
            return
            
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        self.gallery_images = sorted([f for f in os.listdir(folder_b) if f.lower().endswith(valid_extensions)])
        
        if self.gallery_images:
            if self.current_gallery_idx < 0 or self.current_gallery_idx >= len(self.gallery_images):
                self.current_gallery_idx = len(self.gallery_images) - 1
        self.update_gallery_view()

    def update_gallery_view(self):
        if not self.gallery_images or self.current_gallery_idx < 0:
            self.lbl_gallery_status.configure(text=t('gallery_no_images'))
            self.ab_widget.set_images(None, None)
            return
            
        filename = self.gallery_images[self.current_gallery_idx]
        self.lbl_gallery_status.configure(text=t('gallery_image_info', current=self.current_gallery_idx + 1, total=len(self.gallery_images), filename=filename))
        
        folder_a = self.ent_folder_a.get().strip()
        folder_b = self.ent_folder_b.get().strip()
        
        path_a = os.path.join(folder_a, filename)
        path_b = os.path.join(folder_b, filename)
        
        # Automatically fall back if original image A doesn't exist
        self.ab_widget.set_images(path_a if os.path.exists(path_a) else None, path_b)

    def next_image(self):
        if self.gallery_images:
            self.current_gallery_idx = (self.current_gallery_idx + 1) % len(self.gallery_images)
            self.update_gallery_view()
            
    def prev_image(self):
        if self.gallery_images:
            self.current_gallery_idx = (self.current_gallery_idx - 1) % len(self.gallery_images)
            self.update_gallery_view()

    # --- Threading & Queues ---
    def append_log(self, message):
        self.log_queue.put(message)

    def update_progress(self, value, maximum):
        self.progress_queue.put((value, maximum))

    def trigger_gallery_sync(self):
        self.gallery_sync_queue.put(True)

    def check_queues(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_area.configure(state="normal")
            self.log_area.insert("end", msg + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
            self.lbl_status.configure(text=msg.split(":")[-1].strip()[:20] + "...")
            
        while not self.progress_queue.empty():
            val, maximum = self.progress_queue.get_nowait()
            if maximum > 0:
                self.progress_bar.set(val / maximum)
                
        while not self.gallery_sync_queue.empty():
            self.gallery_sync_queue.get_nowait()
            self.load_gallery_from_disk()
                
        self.after(100, self.check_queues)

    # --- ComfyUI Execution ---
    def start_processing(self):
        if self.is_running:
            return

        url = self.ent_url.get().strip()
        folder_a = self.ent_folder_a.get().strip()
        folder_b = self.ent_folder_b.get().strip()
        api_json = self.ent_json.get().strip()
        load_id = self.ent_load_id.get().strip()
        save_id = self.ent_save_id.get().strip()
        prefix = self.ent_prefix.get().strip()

        if not all([url, folder_a, folder_b, api_json, load_id, save_id]):
            messagebox.showwarning(t('msgbox_input_error_title'), t('msgbox_input_error_message'))
            return

        if not os.path.exists(folder_a) or not os.path.exists(api_json):
            messagebox.showerror(t('msgbox_path_error_title'), t('msgbox_path_error_message'))
            return

        self.is_running = True
        self.btn_start.configure(state="disabled", text=t('btn_processing'))
        self.progress_bar.set(0)
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

        threading.Thread(target=self.process_workflow_thread, args=(url, folder_a, folder_b, api_json, load_id, save_id, prefix), daemon=True).start()

    def process_workflow_thread(self, url, folder_a, folder_b, api_json, load_id, save_id, prefix=""):
        try:
            os.makedirs(folder_b, exist_ok=True)
            
            self.append_log(t('log_initializing'))
            api = ComfyUIAPI(server_address=url)
            
            if not api.check_connection():
                self.append_log(t('log_connection_failed'))
                self.finish_processing()
                return
                
            with open(api_json, "r", encoding="utf-8") as f:
                workflow_template = json.load(f)

            valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
            images_to_process = [f for f in os.listdir(folder_a) if f.lower().endswith(valid_extensions)]

            if not images_to_process:
                self.append_log(t('log_no_images_found', folder=folder_a))
                self.finish_processing()
                return

            self.append_log(t('log_connected', count=len(images_to_process)))
            if prefix:
                self.append_log(t('log_prefix_info', prefix=prefix))

            for i, filename in enumerate(images_to_process, 1):
                self.append_log(t('log_separator'))
                self.append_log(t('log_processing_image', current=i, total=len(images_to_process), filename=filename))
                self.update_progress(0, 1) 
                
                input_filepath = os.path.join(folder_a, filename)
                # Prepend the custom prefix to the output filename
                output_filename = f"{prefix}{filename}" if prefix else filename
                output_filepath = os.path.join(folder_b, output_filename)

                self.append_log(t('log_uploading'))
                uploaded_name = api.upload_image(input_filepath)

                workflow = workflow_template.copy()
                if load_id in workflow and "inputs" in workflow[load_id]:
                    workflow[load_id]["inputs"]["image"] = uploaded_name
                if save_id in workflow and "inputs" in workflow[save_id]:
                    # Prepend custom prefix to the filename for ComfyUI output
                    name_without_ext = str(filename).rsplit('.', 1)[0]
                    workflow[save_id]["inputs"]["filename_prefix"] = f"{prefix}{name_without_ext}" if prefix else name_without_ext

                self.append_log(t('log_executing'))
                outputs = api.process_prompt_ws(
                    prompt=workflow,
                    status_callback=lambda val, max_val: self.update_progress(val, max_val),
                    log_callback=lambda msg: self.append_log(msg)
                )

                if outputs and save_id in outputs and "images" in outputs[save_id]:
                    out_info = outputs[save_id]["images"][0]
                    img_data = api.get_image(out_info["filename"], out_info.get("subfolder", ""), out_info.get("type", "output"))
                    
                    with open(output_filepath, "wb") as f:
                        f.write(img_data)
                        
                    self.append_log(t('log_saved', filename=output_filename))
                    self.trigger_gallery_sync()
                else:
                    self.append_log(t('log_warning_no_output', node_id=save_id))

            self.append_log(t('log_completed'))
            messagebox.showinfo(t('msgbox_done_title'), t('msgbox_done_message'))

        except Exception as e:
            self.append_log(t('log_fatal_error', error=str(e)))
            messagebox.showerror(t('msgbox_error_title'), t('msgbox_error_message', error=str(e)))
            
        finally:
            self.finish_processing()

    def finish_processing(self):
        self.is_running = False
        self.btn_start.configure(state="normal", text=t('btn_start'))
        self.lbl_status.configure(text=t('status_finished'))
        self.progress_bar.set(1)

if __name__ == "__main__":
    app = ModernComfyUIApp()
    app.mainloop()
