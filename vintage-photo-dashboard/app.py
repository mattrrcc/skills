import os
import io
import json
import base64
import time
import queue
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# SSE client registry
sse_clients: dict[str, queue.Queue] = {}

# Available Gemini models (best to fastest)
GEMINI_MODELS = {
    "gemini-2.0-flash-exp": "Gemini 2.0 Flash Exp — Best accuracy (Recommended)",
    "gemini-2.0-flash": "Gemini 2.0 Flash — Fast & accurate",
    "gemini-1.5-pro": "Gemini 1.5 Pro — High accuracy",
    "gemini-1.5-flash": "Gemini 1.5 Flash — Balanced speed/quality",
}
DEFAULT_MODEL = "gemini-2.0-flash-exp"

VINTAGE_STYLES = {
    "polaroid": {
        "name": "Polaroid Instant",
        "prompt": "You are a professional 90s Polaroid instant photography expert. Analyze this photo and describe in vivid detail how it would look as a vintage Polaroid instant photograph from the early 1990s: slightly overexposed, warm yellowish tones, soft focus edges, characteristic Polaroid color shifts with slightly washed-out blues and boosted warm tones, subtle vignetting, that distinctive Polaroid film border look. Describe the mood, the nostalgic feeling, and give 5 specific vintage editing tips to recreate this look. Format as JSON: {\"style_name\": \"Polaroid Instant\", \"mood\": \"...\", \"color_palette\": [...], \"characteristics\": [...], \"editing_tips\": [...], \"era\": \"Early 1990s\", \"film_type\": \"Polaroid 600\"}",
        "icon": "📷",
        "color": "#F4D03F"
    },
    "film_grain": {
        "name": "35mm Film Grain",
        "prompt": "You are a 90s analog photography darkroom expert. Analyze this photo and describe how it would look shot on Kodak Gold 200 or Fuji Superia 400 film from 1992-1998: heavy film grain especially in shadows, slightly desaturated with a green-yellow cast, slightly underexposed with crushed blacks, authentic film grain texture, chromatic aberration at edges, light leaks possibility. Describe the atmosphere and give 5 specific darkroom techniques. Format as JSON: {\"style_name\": \"35mm Film Grain\", \"mood\": \"...\", \"color_palette\": [...], \"characteristics\": [...], \"editing_tips\": [...], \"era\": \"Mid 1990s\", \"film_type\": \"Kodak Gold 200\"}",
        "icon": "🎞️",
        "color": "#E67E22"
    },
    "vhs_aesthetic": {
        "name": "VHS Aesthetic",
        "prompt": "You are a 90s VHS video and photography culture expert. Analyze this photo and describe how it would look if captured via VHS camcorder from 1993-1997 then printed: scan lines, color bleeding, slightly saturated but muddy colors, tracking artifacts, date/time stamp overlay style, that distinctive VHS color palette with boosted reds and slightly blurry quality. Give 5 tips for recreating this look digitally. Format as JSON: {\"style_name\": \"VHS Aesthetic\", \"mood\": \"...\", \"color_palette\": [...], \"characteristics\": [...], \"editing_tips\": [...], \"era\": \"Early-Mid 1990s\", \"film_type\": \"VHS Camcorder\"}",
        "icon": "📼",
        "color": "#8E44AD"
    },
    "disposable_camera": {
        "name": "Disposable Camera",
        "prompt": "You are a 90s disposable camera and casual photography expert. Analyze this photo and describe how it would look taken on a Kodak FunSaver or Fuji QuickSnap disposable camera from 1994-1999: harsh built-in flash causing red-eye and flat lighting, slight motion blur, colors that are slightly off especially greens and blues, that authentic 'party photo' quality with genuine imperfections. Give 5 specific techniques to recreate this authentic look. Format as JSON: {\"style_name\": \"Disposable Camera\", \"mood\": \"...\", \"color_palette\": [...], \"characteristics\": [...], \"editing_tips\": [...], \"era\": \"Late 1990s\", \"film_type\": \"Kodak FunSaver\"}",
        "icon": "📸",
        "color": "#27AE60"
    },
    "slide_film": {
        "name": "Slide/Reversal Film",
        "prompt": "You are a 90s professional slide film photography expert. Analyze this photo and describe how it would look shot on Kodachrome 64 or Ektachrome 100 slide film from 1990-1995: rich saturated colors especially reds and blues, very sharp and detailed, high contrast with deep shadows, that iconic Kodachrome warmth and richness, slight color shift toward reds in skin tones. Give 5 professional techniques for recreating this prestigious look. Format as JSON: {\"style_name\": \"Slide/Reversal Film\", \"mood\": \"...\", \"color_palette\": [...], \"characteristics\": [...], \"editing_tips\": [...], \"era\": \"Early 1990s\", \"film_type\": \"Kodachrome 64\"}",
        "icon": "🎨",
        "color": "#C0392B"
    }
}


def send_sse_event(client_id: str, event_type: str, data: dict):
    if client_id in sse_clients:
        sse_clients[client_id].put({
            "event": event_type,
            "data": json.dumps(data)
        })


def process_image_with_gemini(client_id: str, image_data: bytes, style_key: str, api_key: str, model_id: str = DEFAULT_MODEL):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)

        style = VINTAGE_STYLES[style_key]

        send_sse_event(client_id, "progress", {
            "stage": "analyzing",
            "message": f"Loading your photo into the darkroom...",
            "progress": 15
        })
        time.sleep(0.5)

        img = Image.open(io.BytesIO(image_data))
        if img.mode == "RGBA":
            img = img.convert("RGB")

        max_size = (1024, 1024)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=85)
        img_buffer.seek(0)
        img_bytes = img_buffer.read()

        send_sse_event(client_id, "progress", {
            "stage": "processing",
            "message": f"Channeling the {style['name']} spirit...",
            "progress": 40
        })

        img_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_bytes).decode()
        }

        send_sse_event(client_id, "progress", {
            "stage": "generating",
            "message": "Developing in the vintage darkroom...",
            "progress": 65
        })

        response = model.generate_content(
            [style["prompt"], img_part],
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=1024,
            )
        )

        send_sse_event(client_id, "progress", {
            "stage": "finalizing",
            "message": "Adding the finishing vintage touches...",
            "progress": 85
        })

        result_text = response.text.strip()
        # Extract JSON from markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        try:
            result_data = json.loads(result_text)
        except json.JSONDecodeError:
            result_data = {
                "style_name": style["name"],
                "mood": "Nostalgic and evocative",
                "color_palette": ["Warm yellows", "Faded blues", "Earthy browns"],
                "characteristics": ["Film grain", "Soft focus", "Warm tones"],
                "editing_tips": [result_text],
                "era": "1990s",
                "film_type": style["name"]
            }

        # Add base64 preview of original
        original_b64 = base64.b64encode(img_bytes).decode()

        send_sse_event(client_id, "complete", {
            "style": style_key,
            "style_name": style["name"],
            "style_icon": style["icon"],
            "result": result_data,
            "original_preview": f"data:image/jpeg;base64,{original_b64}",
            "progress": 100
        })

    except Exception as e:
        send_sse_event(client_id, "error", {
            "message": str(e),
            "stage": "error"
        })


@app.route("/")
def index():
    prefill_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "")
    return render_template("index.html", styles=VINTAGE_STYLES, prefill_key=prefill_key)


@app.route("/api/styles")
def get_styles():
    return jsonify(VINTAGE_STYLES)


@app.route("/stream/<client_id>")
def stream(client_id: str):
    def event_generator():
        q: queue.Queue = queue.Queue()
        sse_clients[client_id] = q

        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'client_id': client_id})}\n\n"

        try:
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                    if msg["event"] in ("complete", "error"):
                        break
                except queue.Empty:
                    yield f"event: heartbeat\ndata: {json.dumps({'ts': time.time()})}\n\n"
        finally:
            sse_clients.pop(client_id, None)

    return Response(
        stream_with_context(event_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.route("/api/models")
def get_models():
    return jsonify(GEMINI_MODELS)


@app.route("/api/process", methods=["POST"])
def process_photo():
    api_key = request.form.get("api_key", "").strip()
    style_key = request.form.get("style", "polaroid")
    client_id = request.form.get("client_id", "")
    model_id = request.form.get("model", DEFAULT_MODEL)
    if model_id not in GEMINI_MODELS:
        model_id = DEFAULT_MODEL

    if not api_key:
        return jsonify({"error": "Google AI Studio API key required"}), 400

    if style_key not in VINTAGE_STYLES:
        return jsonify({"error": "Invalid style selected"}), 400

    if "photo" not in request.files:
        return jsonify({"error": "No photo uploaded"}), 400

    photo = request.files["photo"]
    if not photo.filename:
        return jsonify({"error": "No photo selected"}), 400

    allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    ext = Path(photo.filename).suffix.lower()
    if ext not in allowed:
        return jsonify({"error": f"File type {ext} not supported"}), 400

    image_data = photo.read()

    thread = threading.Thread(
        target=process_image_with_gemini,
        args=(client_id, image_data, style_key, api_key, model_id),
        daemon=True
    )
    thread.start()

    return jsonify({"status": "processing", "client_id": client_id})


@app.route("/api/analyze-text", methods=["POST"])
def analyze_text():
    """Generate a vintage photography style description without an image."""
    data = request.get_json()
    api_key = data.get("api_key", "").strip()
    style_key = data.get("style", "polaroid")
    scene_description = data.get("scene", "")
    model_id = data.get("model", DEFAULT_MODEL)
    if model_id not in GEMINI_MODELS:
        model_id = DEFAULT_MODEL

    if not api_key:
        return jsonify({"error": "API key required"}), 400

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)
        style = VINTAGE_STYLES[style_key]

        prompt = f"""You are a 90s vintage photography expert. Someone wants to recreate a {style['name']} style shot of: "{scene_description}".

Give them a complete vintage photography guide. Format as JSON:
{{
  "style_name": "{style['name']}",
  "scene": "{scene_description}",
  "composition_tips": ["tip1", "tip2", "tip3"],
  "lighting_advice": "detailed lighting setup for authentic 90s look",
  "camera_settings": {{"aperture": "f/...", "shutter": "1/...", "iso": "..."}},
  "color_palette": ["color1", "color2", "color3", "color4"],
  "post_processing": ["step1", "step2", "step3", "step4", "step5"],
  "era_context": "Brief cultural context about this style in the 90s",
  "film_type": "{style['name']}"
}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result_data = json.loads(result_text)
        return jsonify({"result": result_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, threaded=True)
