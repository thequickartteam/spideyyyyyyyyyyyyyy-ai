import os

import requests
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

API_URL = "https://api.deepai.org/api/text2img"
API_HEADER = "api-key"

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DeepAI Image Studio</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: #0b1020;
      color: #f4f5fb;
      font: 15px/1.5 system-ui, sans-serif;
    }
    .topbar {
      padding: 18px 6%;
      border-bottom: 1px solid #262d43;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand { font-weight: 750; letter-spacing: .3px; }
    .badge {
      color: #a8f0cf;
      background: #123629;
      padding: 5px 10px;
      border-radius: 20px;
      font-size: 12px;
    }
    main {
      width: min(1100px, 92%);
      margin: 42px auto;
      display: grid;
      grid-template-columns: minmax(300px, .9fr) minmax(350px, 1.1fr);
      gap: 22px;
    }
    .card {
      padding: 24px;
      border: 1px solid #29324a;
      border-radius: 16px;
      background: #141b2e;
      box-shadow: 0 18px 50px #0003;
    }
    h1 { margin: 0 0 8px; font-size: 28px; }
    .muted { color: #a4adc3; }
    label { display: block; margin: 20px 0 7px; font-weight: 650; }
    input, textarea {
      width: 100%;
      color: #fff;
      background: #0d1323;
      border: 1px solid #303a55;
      border-radius: 9px;
      padding: 12px;
      font: inherit;
      outline: none;
    }
    input:focus, textarea:focus { border-color: #9b7bff; }
    textarea { min-height: 145px; resize: vertical; }
    button {
      width: 100%;
      border: 0;
      border-radius: 9px;
      padding: 13px 16px;
      margin-top: 18px;
      color: #fff;
      background: linear-gradient(100deg, #8057ff, #bd5bf5);
      font: inherit;
      font-weight: 750;
      cursor: pointer;
    }
    button:disabled { opacity: .6; cursor: wait; }
    .request {
      margin-top: 22px;
      padding: 14px;
      border-radius: 10px;
      background: #0d1323;
      border: 1px solid #29324a;
      font-size: 13px;
    }
    .request strong { display: block; margin-bottom: 7px; }
    code {
      color: #9fe8c0;
      overflow-wrap: anywhere;
    }
    .preview {
      min-height: 420px;
      display: grid;
      place-items: center;
      overflow: hidden;
      border: 1px dashed #394461;
      border-radius: 12px;
      background:
        radial-gradient(ellipse at 35% 25%, #25234a, transparent 55%),
        #0d1323;
    }
    .preview img { display: block; max-width: 100%; max-height: 620px; }
    .placeholder { padding: 30px; text-align: center; color: #969fb5; }
    #status { margin-top: 12px; min-height: 22px; color: #c6b7ff; }
    details { margin-top: 18px; }
    summary { cursor: pointer; color: #bec6d9; }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      max-height: 240px;
      overflow: auto;
      color: #b7c7e8;
      background: #0d1323;
      padding: 12px;
      border-radius: 8px;
      font-size: 12px;
    }
    @media (max-width: 760px) {
      main { grid-template-columns: 1fr; margin: 22px auto; }
      .preview { min-height: 300px; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">✦ DeepAI Image Studio</div>
    <div class="badge">Text to Image</div>
  </header>

  <main>
    <section class="card">
      <h1>Create an image</h1>
      <div class="muted">Describe what you want to see. Your API key is kept in this browser tab and sent to this app’s server for the API request.</div>

      <form id="form">
        <label for="key">DeepAI API key</label>
        <input id="key" type="password" placeholder="Enter your API key" autocomplete="off" required>

        <label for="prompt">Image prompt</label>
        <textarea id="prompt" placeholder="A tiny glass greenhouse on a floating island at sunrise, cinematic lighting..." required></textarea>

        <button id="submit" type="submit">Generate image</button>
      </form>

      <div id="status" role="status"></div>

      <div class="request">
        <strong>Request details</strong>
        URL: <code>{{ api_url }}</code><br>
        Header: <code>{{ api_header }}: your API key</code><br>
        Form field: <code>text=your prompt</code>
      </div>

      <details>
        <summary>Show equivalent cURL</summary>
        <pre id="curl"></pre>
      </details>
    </section>

    <section class="card">
      <h1>Preview</h1>
      <div class="muted" style="margin-bottom:16px">Your generated image will appear here.</div>
      <div id="preview" class="preview">
        <div class="placeholder">Your creation is waiting to happen ✨</div>
      </div>
      <details>
        <summary>Show API response</summary>
        <pre id="response">No request yet.</pre>
      </details>
    </section>
  </main>

<script>
const form = document.getElementById("form");
const keyInput = document.getElementById("key");
const promptInput = document.getElementById("prompt");
const submitButton = document.getElementById("submit");
const statusBox = document.getElementById("status");
const preview = document.getElementById("preview");
const responseBox = document.getElementById("response");
const curlBox = document.getElementById("curl");

keyInput.value = sessionStorage.getItem("deepai_key") || "";

function updateCurl() {
  const prompt = promptInput.value || "YOUR_TEXT_HERE";
  curlBox.textContent =
`curl \\
  -F 'text=${prompt.replaceAll("'", "'\\\\''")}' \\
  -H '{{ api_header }}: YOUR_PRIVATE_API_KEY' \\
  {{ api_url }}`;
}

promptInput.addEventListener("input", updateCurl);
updateCurl();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const key = keyInput.value.trim();
  const prompt = promptInput.value.trim();
  if (!key || !prompt) return;

  sessionStorage.setItem("deepai_key", key);
  submitButton.disabled = true;
  submitButton.textContent = "Generating…";
  statusBox.textContent = "Sending request to DeepAI…";
  responseBox.textContent = "Waiting for response…";

  const data = new FormData();
  data.append("key", key);
  data.append("text", prompt);

  try {
    const response = await fetch("/generate", { method: "POST", body: data });
    const result = await response.json();
    responseBox.textContent = JSON.stringify(result, null, 2);

    if (!response.ok) {
      throw new Error(result.error || "Request failed");
    }

    const imageUrl = result.output_url;
    if (!imageUrl) {
      throw new Error("The API response did not include an output_url.");
    }

    const image = document.createElement("img");
    image.alt = prompt;
    image.src = imageUrl;
    preview.replaceChildren(image);
    statusBox.textContent = "Image generated successfully.";
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Generate image";
  }
});
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(
        PAGE,
        api_url=API_URL,
        api_header=API_HEADER,
    )


@app.post("/generate")
def generate():
    api_key = request.form.get("key", "").strip()
    prompt = request.form.get("text", "").strip()

    if not api_key or not prompt:
        return jsonify({"error": "API key and prompt are required"}), 400

    try:
        # Matches the documented cURL pattern:
        # -F 'text=...' -H 'api-key: ...' https://api.deepai.org/api/text2img
        upstream = requests.post(
            API_URL,
            headers={API_HEADER: api_key},
            data={"text": prompt},
            timeout=120,
        )

        try:
            result = upstream.json()
        except ValueError:
            result = {"response_text": upstream.text}

        if not upstream.ok:
            return jsonify({
                "error": "DeepAI returned an error.",
                "upstream_status": upstream.status_code,
                "details": result,
            }), upstream.status_code

        return jsonify(result)

    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach DeepAI: {exc}"}), 502


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "8080")),
        debug=False,
    )
