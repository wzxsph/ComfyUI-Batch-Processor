# ==============================================================================
# 科学与学术视觉自动化生成系统 - 方案一 (ComfyUI API + 后期矢量覆写)
# ==============================================================================
# 依赖安装: pip install requests pillow
# 使用说明: 
# 1. 启动您的本地 ComfyUI (默认地址 http://127.0.0.1:8188)
# 2. 确保您拥有标准模型 "sd_xl_base_1.0.safetensors" (放置于 models/checkpoints)
# 3. 运行此脚本: python PointNet_Auto_Pipeline.py
# ==============================================================================

import json
import urllib.request
import urllib.parse
import time
import os
from PIL import Image, ImageDraw, ImageFont

# --- 配置区 ---
COMFYUI_URL = "http://127.0.0.1:8000"
CHECKPOINT_NAME = "sd_xl_base_1.0.safetensors" # 请替换为您实际拥有的 SDXL 模型名
OUTPUT_FILENAME = "Final_PointNet_Architecture.png"

# ==============================================================================
# 1. 定义 ComfyUI 的原生区域扩散工作流 (无需求任何第三方自定义节点)
# ==============================================================================
prompt_workflow = {
    # 加载 SDXL 模型
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT_NAME}},
    
    # 创建 1536x512 的宽幅画板 (适合架构图)
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1536, "height": 512, "batch_size": 1}},
    
    # 区域 1：左侧 512x512 (输入点云)
    "10": {"class_type": "CLIPTextEncode", "inputs": {"text": "(masterpiece, best quality), a glowing blue 3D point cloud scattered in space, pure white background, scientific illustration", "clip": ["4", 1]}},
    "11": {"class_type": "ConditioningSetArea", "inputs": {"width": 512, "height": 512, "x": 0, "y": 0, "strength": 1.0, "conditioning": ["10", 0]}},
    
    # 区域 2：中间 512x512 (特征提取圆柱体)
    "12": {"class_type": "CLIPTextEncode", "inputs": {"text": "(masterpiece), two translucent 3D blue glass cylinders standing vertically, soft lighting, pure white background", "clip": ["4", 1]}},
    "13": {"class_type": "ConditioningSetArea", "inputs": {"width": 512, "height": 512, "x": 512, "y": 0, "strength": 1.0, "conditioning": ["12", 0]}},
    
    # 区域 3：右侧 512x512 (全连接层红色色块)
    "14": {"class_type": "CLIPTextEncode", "inputs": {"text": "(masterpiece), abstract red glowing 3D blocks, neural network dense layers, pure white background", "clip": ["4", 1]}},
    "15": {"class_type": "ConditioningSetArea", "inputs": {"width": 512, "height": 512, "x": 1024, "y": 0, "strength": 1.0, "conditioning": ["14", 0]}},
    
    # 组合所有区域的正向提示词
    "16": {"class_type": "ConditioningCombine", "inputs": {"conditioning_1": ["11", 0], "conditioning_2": ["13", 0]}},
    "17": {"class_type": "ConditioningCombine", "inputs": {"conditioning_1": ["16", 0], "conditioning_2": ["15", 0]}},
    
    # 负向提示词：绝对禁止模型生成文字、线条和箭头！
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "text, typography, letters, fonts, words, messy lines, arrows, watermarks, dark background, ugly topology", "clip": ["4", 1]}},
    
    # KSampler 采样器
    "3": {"class_type": "KSampler", "inputs": {"seed": int(time.time()), "steps": 30, "cfg": 7.5, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["4", 0], "positive": ["17", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
    
    # VAE 解码与保存
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "PointNet_Base", "images": ["8", 0]}}
}

# ==============================================================================
# 2. 与 ComfyUI 交互的通信函数
# ==============================================================================
def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    req = urllib.request.Request(f"{COMFYUI_URL}/view?{url_values}")
    response = urllib.request.urlopen(req)
    return response.read()

# ==============================================================================
# 3. 图像覆写（后处理）：在渲染好的 3D 图上绘制学术文字和箭头
# ==============================================================================
def draw_arrow(draw, ptA, ptB, width=3, color="black"):
    draw.line((ptA, ptB), fill=color, width=width)
    # 简易绘制箭头头部
    import math
    angle = math.atan2(ptB[1] - ptA[1], ptB[0] - ptA[0])
    arrow_size = 15
    p1 = (ptB[0] - arrow_size * math.cos(angle - math.pi/6), ptB[1] - arrow_size * math.sin(angle - math.pi/6))
    p2 = (ptB[0] - arrow_size * math.cos(angle + math.pi/6), ptB[1] - arrow_size * math.sin(angle + math.pi/6))
    draw.polygon([ptB, p1, p2], fill=color)

def post_process_image(image_data):
    print(">> 开始进行矢量文字与箭头覆写...")
    
    # 保存临时文件
    with open("temp_base.png", "wb") as f:
        f.write(image_data)
        
    img = Image.open("temp_base.png").convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    # 尝试加载标准无衬线字体（若无则使用默认）
    try:
        font_title = ImageFont.truetype("arial.ttf", 40)
        font_text = ImageFont.truetype("arial.ttf", 24)
        font_math = ImageFont.truetype("times.ttf", 20)
    except:
        font_title = font_text = font_math = ImageFont.load_default()

    # 1. 绘制箭头 (连接三个区域)
    draw_arrow(draw, (400, 256), (550, 256), width=4, color="#374151")
    draw_arrow(draw, (900, 256), (1080, 256), width=4, color="#374151")
    
    # 2. 写入文字标签
    # 标题
    draw.text((300, 30), "Hierarchical Point Set Feature Learning (PointNet++)", fill="#111827", font=font_title)
    
    # 左侧：点云
    draw.text((150, 420), "Input Point Cloud", fill="#1f2937", font=font_text)
    draw.text((180, 455), "N × (d + C)", fill="#4b5563", font=font_math)
    
    # 中间：SA层
    draw.text((650, 420), "Set Abstraction Levels", fill="#1f2937", font=font_text)
    draw.text((680, 455), "N_i × (d + C_i)", fill="#4b5563", font=font_math)
    
    # 右侧：全连接
    draw.text((1180, 420), "Fully Connected", fill="#1f2937", font=font_text)
    draw.text((1190, 455), "Classification", fill="#4b5563", font=font_math)
    
    img.save(OUTPUT_FILENAME)
    os.remove("temp_base.png")
    print(f">> 成功！最终论文配图已保存为: {OUTPUT_FILENAME}")

# ==============================================================================
# 主执行流程
# ==============================================================================
if __name__ == "__main__":
    print(">> 正在向 ComfyUI 发送区域生成任务...")
    prompt_id = queue_prompt(prompt_workflow)['prompt_id']
    
    print(f">> 任务已提交 (ID: {prompt_id})，等待 ComfyUI 渲染 3D 元素...")
    
    # 轮询获取结果
    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            outputs = history[prompt_id]['outputs']
            # 找到 SaveImage 节点的输出
            for node_id in outputs:
                node_output = outputs[node_id]
                if 'images' in node_output:
                    image_info = node_output['images'][0]
                    image_data = get_image(image_info['filename'], image_info['subfolder'], image_info['type'])
                    post_process_image(image_data)
            break
        else:
            time.sleep(2)
            print("   渲染中，请稍候...")