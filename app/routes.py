from flask import Blueprint, render_template, request
import os
import requests
import json
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
VIDEO_FOLDER = 'app/static/videos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# preload mô hình (giả lập)
def preload_model():
    print("Preloading models...")
    required_files = [
        '../models/stable-diffusion/v1-5-pruned.ckpt',
        '../models/animatediff/mm_sd_v15_v2.ckpt',
        '../models/controlnet/control_sd15_canny.pth',
        '../models/vae/vae-ft-mse-840000-ema-pruned.ckpt'
    ]
    for path in required_files:
        if not os.path.exists(path):
            print(f"Thiếu mô hình: {path}")
        else:
            print(f"Đã tìm thấy: {path}")

preload_model()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/', methods=['GET', 'POST'])
def index():
    video_path = None
    image_path = None

    if request.method == 'POST':
        prompt = request.form.get('prompt')
        duration = int(request.form.get('duration'))
        fps = 8
        frame_count = duration * fps

        uploaded_file = request.files.get('image')
        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(image_path)

        # Đọc workflow.json mẫu
        with open('workflow.json', 'r') as f:
            workflow = json.load(f)

        # Cập nhật workflow theo input
        workflow['prompt'] = prompt
        workflow['frame_count'] = frame_count
        workflow['fps'] = fps
        workflow['controlnet']['image'] = image_path if image_path else None

        try:
            # Gửi request đến ComfyUI API
            response = requests.post("http://127.0.0.1:8188/prompt", json=workflow)
            result = response.json()

            # Lấy ID job từ ComfyUI
            job_id = result.get("prompt_id")
            if job_id:
                # Poll trạng thái cho đến khi hoàn tất
                status_url = f"http://127.0.0.1:8188/history/{job_id}"
                while True:
                    status_resp = requests.get(status_url)
                    status_data = status_resp.json()
                    if "outputs" in status_data.get(job_id, {}):
                        # Lấy URL video từ outputs
                        outputs = status_data[job_id]["outputs"]
                        video_url = outputs.get("video", [])[0]  # giả sử trả về danh sách
                        if video_url:
                            # Tải video về và lưu vào VIDEO_FOLDER
                            video_resp = requests.get(video_url)
                            video_path = os.path.join(VIDEO_FOLDER, "output.mp4")
                            with open(video_path, "wb") as f:
                                f.write(video_resp.content)
                            break
        except Exception as e:
            print(f"Lỗi khi gửi request đến ComfyUI: {e}")

    return render_template('index.html', video_path=video_path, image_path=image_path)