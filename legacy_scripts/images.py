import os
import json
import time
import requests
import shutil

# ================= 配置区域 =================
# ComfyUI 的运行地址（默认通常是这个）
COMFY_URL = "http://127.0.0.1:8000"

# 文件夹路径配置 (请替换为你自己的实际路径，注意路径中的斜杠需要用双斜杠 \\ 或前加 r)
FOLDER_A = r"./input_images"  # 待处理图片文件夹 (文件夹 A)
FOLDER_B = r"./output_images" # 处理后图片保存文件夹 (文件夹 B)
API_JSON_PATH = r"./workflow_api.json" # 第一步导出的 API 格式工作流文件路径

# 节点 ID 配置 (根据你上传的JSON，我已经帮你找好了)
LOAD_IMAGE_NODE_ID = "202"  # LoadImage 节点的 ID
SAVE_IMAGE_NODE_ID = "136"  # SaveImage 节点的 ID
# ============================================

def upload_image(filepath):
    """将图片上传到 ComfyUI 服务器"""
    with open(filepath, "rb") as f:
        files = {"image": f}
        response = requests.post(f"{COMFY_URL}/upload/image", files=files)
        response.raise_for_status()
        return response.json()["name"] # 返回 ComfyUI 重命名后的文件名

def queue_prompt(prompt_workflow):
    """将工作流发送给 ComfyUI 执行"""
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    response = requests.post(f"{COMFY_URL}/prompt", data=data)
    response.raise_for_status()
    return response.json()["prompt_id"]

def get_history(prompt_id):
    """获取执行历史记录以检查是否完成"""
    response = requests.get(f"{COMFY_URL}/history/{prompt_id}")
    response.raise_for_status()
    return response.json()

def download_image(filename, subfolder, folder_type, save_path):
    """从 ComfyUI 下载生成的图片"""
    url = f"{COMFY_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

def main():
    # 确保输出文件夹存在
    if not os.path.exists(FOLDER_B):
        os.makedirs(FOLDER_B)

    # 读取 API 工作流模板
    with open(API_JSON_PATH, "r", encoding="utf-8") as f:
        workflow_template = json.load(f)

    # 获取文件夹A中所有的图片文件
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    images_to_process = [f for f in os.listdir(FOLDER_A) if f.lower().endswith(valid_extensions)]

    if not images_to_process:
        print(f"在 {FOLDER_A} 中没有找到图片！")
        return

    print(f"找到 {len(images_to_process)} 张图片，开始处理...")

    for i, original_filename in enumerate(images_to_process, 1):
        print(f"\n[{i}/{len(images_to_process)}] 正在处理: {original_filename}")
        input_filepath = os.path.join(FOLDER_A, original_filename)
        output_filepath = os.path.join(FOLDER_B, original_filename) # 保证输出名字与输入名字一致

        try:
            # 1. 上传图片到 ComfyUI
            print("  -> 上传图片中...")
            comfy_input_name = upload_image(input_filepath)

            # 2. 修改工作流中的节点参数
            workflow = workflow_template.copy()
            # 将上传的图片名赋值给 LoadImage 节点
            workflow[LOAD_IMAGE_NODE_ID]["inputs"]["image"] = comfy_input_name
            # 给 SaveImage 节点一个特定的前缀，方便管理（虽然我们最后会重命名）
            workflow[SAVE_IMAGE_NODE_ID]["inputs"]["filename_prefix"] = "auto_batch"

            # 3. 提交任务
            print("  -> 开始生成...")
            prompt_id = queue_prompt(workflow)

            # 4. 轮询等待任务完成
            while True:
                history = get_history(prompt_id)
                if prompt_id in history:
                    # 任务完成
                    history_data = history[prompt_id]
                    # 获取输出图片的信息
                    outputs = history_data.get("outputs", {})
                    if SAVE_IMAGE_NODE_ID in outputs and "images" in outputs[SAVE_IMAGE_NODE_ID]:
                        output_image_info = outputs[SAVE_IMAGE_NODE_ID]["images"][0]
                        out_filename = output_image_info["filename"]
                        out_subfolder = output_image_info.get("subfolder", "")
                        out_type = output_image_info.get("type", "output")
                        
                        # 5. 下载图片并按原名保存到文件夹 B
                        print(f"  -> 生成完毕，正在保存至: {output_filepath}")
                        download_image(out_filename, out_subfolder, out_type, output_filepath)
                    else:
                        print("  -> 警告：未找到输出图片数据，可能是工作流报错。")
                    break
                
                # 每隔 2 秒检查一次
                time.sleep(2)

            print(f"[{original_filename}] 处理完成！")

        except Exception as e:
            print(f"处理 {original_filename} 时发生错误: {e}")

    print("\n所有图片处理完毕！")

if __name__ == "__main__":
    main()