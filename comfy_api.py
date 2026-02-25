import json
import uuid
import requests
import websocket
import urllib.request
import urllib.parse

class ComfyUIAPI:
    """
    Modular wrapper for ComfyUI's REST and WebSocket API.
    Handles image uploading, prompt queueing, and real-time log/progress tracking.
    """
    def __init__(self, server_address="127.0.0.1:8188", client_id=None):
        if server_address.startswith("http://"):
            self.server_address = server_address[7:]
        elif server_address.startswith("https://"):
            self.server_address = server_address[8:]
        else:
            self.server_address = server_address
            
        self.client_id = client_id or str(uuid.uuid4())
        self.ws = websocket.WebSocket()

    def check_connection(self):
        """Check if the ComfyUI server is reachable."""
        try:
            res = requests.get(f"http://{self.server_address}/history", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def upload_image(self, image_path):
        """Uploads an image to ComfyUI and returns the filename."""
        with open(image_path, "rb") as f:
            files = {"image": f}
            res = requests.post(f"http://{self.server_address}/upload/image", files=files)
            res.raise_for_status()
            return res.json()["name"]

    def queue_prompt(self, prompt):
        """Queues a new workflow execution."""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def get_image(self, filename, subfolder, folder_type):
        """Downloads an image from ComfyUI."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
            return response.read()

    def get_history(self, prompt_id):
        """Gets execution history for a particular prompt."""
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())
            
    def process_prompt_ws(self, prompt, status_callback=None, log_callback=None):
        """
        Connects via WebSocket to submit a prompt and listen for real-time progress.
        Blocks until the prompt execution finishes.
        """
        try:
            self.ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
        except Exception as e:
            if log_callback:
                log_callback(f"❌ WS Connect Error: {e}")
            return None
            
        queue_res = self.queue_prompt(prompt)
        prompt_id = queue_res['prompt_id']
        if log_callback:
            log_callback(f"📦 Task queued. Prompt ID: {prompt_id}")
        
        try:
            while True:
                out = self.ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break # Execution done
                        elif data['node'] is not None:
                            if log_callback:
                                log_callback(f"⚡ Executing Node ID: {data['node']}")
                    elif message['type'] == 'progress':
                        data = message['data']
                        if status_callback:
                            status_callback(data['value'], data['max'])
                    elif message['type'] == 'execution_start':
                        if log_callback:
                            log_callback("🚀 Execution started on ComfyUI backend.")
                    elif message['type'] == 'execution_cached':
                        if log_callback:
                            log_callback("♻️ Execution used cache for some nodes.")
                    elif message['type'] == 'execution_interrupted':
                        if log_callback:
                            log_callback("🛑 Execution interrupted!")
                        break
        finally:
            self.ws.close()
            
        history = self.get_history(prompt_id).get(prompt_id, {})
        return history.get('outputs', {})
