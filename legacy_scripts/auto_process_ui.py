import os
import sys
import json
import time
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# ================= 自动安装依赖模块 =================
try:
    import requests
except ImportError:
    # 如果没有 requests 库，弹出提示并自动使用 pip 安装
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("环境初始化", "首次运行需要安装必要的网络库 (requests)。\n\n请点击“确定”，程序将在后台自动安装，请耐心等待几十秒...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        messagebox.showinfo("安装成功", "依赖库安装完毕！即将打开主界面。")
    except Exception as e:
        messagebox.showerror("安装失败", f"自动安装失败，请手动打开命令行输入 'pip install requests'\n\n错误信息: {e}")
        sys.exit(1)
# ===================================================

class ComfyUIBatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ComfyUI 自动化批处理工具")
        self.root.geometry("600x650")
        self.root.resizable(False, False)

        # 设置默认值
        self.url_var = tk.StringVar(value="http://127.0.0.1:8188")
        self.folder_a_var = tk.StringVar()
        self.folder_b_var = tk.StringVar()
        self.api_json_var = tk.StringVar()
        self.load_id_var = tk.StringVar(value="202")
        self.save_id_var = tk.StringVar(value="136")

        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        # 服务器地址配置
        frame_server = tk.LabelFrame(self.root, text="服务器配置", padx=10, pady=10)
        frame_server.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_server, text="ComfyUI 地址:").grid(row=0, column=0, sticky="e")
        tk.Entry(frame_server, textvariable=self.url_var, width=50).grid(row=0, column=1, padx=5)

        # 路径配置
        frame_paths = tk.LabelFrame(self.root, text="路径与文件配置", padx=10, pady=10)
        frame_paths.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_paths, text="输入文件夹 (A):").grid(row=0, column=0, sticky="e", pady=5)
        tk.Entry(frame_paths, textvariable=self.folder_a_var, width=40).grid(row=0, column=1, padx=5)
        tk.Button(frame_paths, text="选择", command=lambda: self.select_folder(self.folder_a_var)).grid(row=0, column=2)

        tk.Label(frame_paths, text="输出文件夹 (B):").grid(row=1, column=0, sticky="e", pady=5)
        tk.Entry(frame_paths, textvariable=self.folder_b_var, width=40).grid(row=1, column=1, padx=5)
        tk.Button(frame_paths, text="选择", command=lambda: self.select_folder(self.folder_b_var)).grid(row=1, column=2)

        tk.Label(frame_paths, text="API 工作流文件:").grid(row=2, column=0, sticky="e", pady=5)
        tk.Entry(frame_paths, textvariable=self.api_json_var, width=40).grid(row=2, column=1, padx=5)
        tk.Button(frame_paths, text="选择", command=self.select_file).grid(row=2, column=2)

        # 节点 ID 配置
        frame_nodes = tk.LabelFrame(self.root, text="高级: 节点 ID 配置", padx=10, pady=10)
        frame_nodes.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_nodes, text="加载图片节点 ID (LoadImage):").grid(row=0, column=0, sticky="e")
        tk.Entry(frame_nodes, textvariable=self.load_id_var, width=10).grid(row=0, column=1, padx=5, sticky="w")
        
        tk.Label(frame_nodes, text="保存图片节点 ID (SaveImage):").grid(row=1, column=0, sticky="e", pady=5)
        tk.Entry(frame_nodes, textvariable=self.save_id_var, width=10).grid(row=1, column=1, padx=5, sticky="w")

        # 操作按钮
        self.btn_start = tk.Button(self.root, text="▶ 开始批量处理", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.start_processing)
        self.btn_start.pack(fill="x", padx=20, pady=10)

        # 日志输出区域
        tk.Label(self.root, text="运行日志:").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(self.root, height=12, state='disabled', bg="#f0f0f0")
        self.log_area.pack(fill="both", padx=10, pady=5, expand=True)

    def select_folder(self, string_var):
        folder = filedialog.askdirectory()
        if folder:
            string_var.set(folder)

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file:
            self.api_json_var.set(file)

    def log(self, message):
        """将信息打印到 UI 界面的日志框中"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def check_comfyui_connection(self, url):
        """检查 ComfyUI 服务器是否联通"""
        try:
            response = requests.get(url, timeout=3)
            return response.status_code == 200
        except:
            return False

    def start_processing(self):
        if self.is_running:
            return

        # 校验输入
        url = self.url_var.get().strip()
        folder_a = self.folder_a_var.get().strip()
        folder_b = self.folder_b_var.get().strip()
        api_json = self.api_json_var.get().strip()
        load_id = self.load_id_var.get().strip()
        save_id = self.save_id_var.get().strip()

        if not all([url, folder_a, folder_b, api_json, load_id, save_id]):
            messagebox.showwarning("提示", "请将所有配置项填写完整！")
            return

        if not os.path.isdir(folder_a):
            messagebox.showerror("错误", "输入文件夹路径不正确！")
            return
            
        if not os.path.isfile(api_json):
            messagebox.showerror("错误", "工作流 API JSON 文件路径不正确！")
            return

        if not self.check_comfyui_connection(url):
            messagebox.showerror("连接失败", f"无法连接到 ComfyUI: {url}\n\n请确保 ComfyUI 已经启动，并检查地址和端口是否正确！")
            return

        self.is_running = True
        self.btn_start.config(state="disabled", text="处理中...")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

        # 使用子线程运行批处理，防止界面卡死
        threading.Thread(target=self.process_workflow, args=(url, folder_a, folder_b, api_json, load_id, save_id), daemon=True).start()

    def process_workflow(self, url, folder_a, folder_b, api_json, load_id, save_id):
        try:
            # 确保输出文件夹存在
            if not os.path.exists(folder_b):
                os.makedirs(folder_b)

            # 读取 API 工作流模板
            with open(api_json, "r", encoding="utf-8") as f:
                workflow_template = json.load(f)

            valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
            images_to_process = [f for f in os.listdir(folder_a) if f.lower().endswith(valid_extensions)]

            if not images_to_process:
                self.log(f"在 {folder_a} 中没有找到支持的图片文件！")
                self.finish_processing()
                return

            self.log(f"=== 成功连接到 ComfyUI ===")
            self.log(f"找到 {len(images_to_process)} 张图片，开始处理...\n")

            for i, original_filename in enumerate(images_to_process, 1):
                self.log(f"[{i}/{len(images_to_process)}] 正在处理: {original_filename}")
                input_filepath = os.path.join(folder_a, original_filename)
                output_filepath = os.path.join(folder_b, original_filename)

                try:
                    # 1. 上传图片
                    self.log("  -> 上传图片中...")
                    with open(input_filepath, "rb") as f:
                        response = requests.post(f"{url}/upload/image", files={"image": f})
                        response.raise_for_status()
                        comfy_input_name = response.json()["name"]

                    # 2. 修改参数
                    workflow = workflow_template.copy()
                    workflow[load_id]["inputs"]["image"] = comfy_input_name
                    workflow[save_id]["inputs"]["filename_prefix"] = "auto_batch"

                    # 3. 提交任务
                    self.log("  -> 发送工作流任务...")
                    p = {"prompt": workflow}
                    response = requests.post(f"{url}/prompt", data=json.dumps(p).encode('utf-8'))
                    response.raise_for_status()
                    prompt_id = response.json()["prompt_id"]

                    # 4. 轮询等待
                    self.log("  -> 正在生成图片，请等待...")
                    while True:
                        res = requests.get(f"{url}/history/{prompt_id}")
                        res.raise_for_status()
                        history = res.json()

                        if prompt_id in history:
                            history_data = history[prompt_id]
                            outputs = history_data.get("outputs", {})
                            
                            if save_id in outputs and "images" in outputs[save_id]:
                                output_image_info = outputs[save_id]["images"][0]
                                out_filename = output_image_info["filename"]
                                out_subfolder = output_image_info.get("subfolder", "")
                                out_type = output_image_info.get("type", "output")
                                
                                # 5. 下载图片
                                dl_url = f"{url}/view?filename={out_filename}&subfolder={out_subfolder}&type={out_type}"
                                dl_res = requests.get(dl_url, stream=True)
                                dl_res.raise_for_status()
                                
                                with open(output_filepath, "wb") as f:
                                    dl_res.raw.decode_content = True
                                    shutil.copyfileobj(dl_res.raw, f)
                                
                                self.log(f"  -> 生成完毕！已保存为: {original_filename}\n")
                            else:
                                self.log("  -> ⚠️ 警告：任务已完成，但未找到输出图片数据。请检查 ComfyUI 是否报错。\n")
                            break
                        
                        time.sleep(2) # 每隔2秒查一次

                except Exception as e:
                    self.log(f"  -> ❌ 处理失败: {e}\n")

            self.log("=== 所有图片处理完毕！ ===")
            messagebox.showinfo("完成", "所有图片批量处理完成！")

        except Exception as e:
            self.log(f"程序运行发生严重错误: {e}")
            messagebox.showerror("错误", f"发生错误:\n{e}")

        finally:
            self.finish_processing()

    def finish_processing(self):
        self.is_running = False
        self.btn_start.config(state="normal", text="▶ 开始批量处理")

if __name__ == "__main__":
    root = tk.Tk()
    app = ComfyUIBatchApp(root)
    root.mainloop()