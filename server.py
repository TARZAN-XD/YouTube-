from flask import Flask, request, jsonify, send_file, render_template_string
from pytube import YouTube
import os

app = Flask(__name__)

# 🎨 HTML مطور + اختيار الجودة
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎞 محمّل يوتيوب</title>
  <style>
    body { font-family: 'Tahoma', sans-serif; background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color: #fff; text-align: center; }
    .box { margin: 60px auto; max-width: 550px; padding: 25px; background: rgba(0,0,0,0.6); border-radius: 16px; box-shadow: 0 6px 25px rgba(0,0,0,.5); }
    h1 { margin-bottom: 10px; color: #f5c542; }
    input, select { width: 100%; padding: 12px; border: none; border-radius: 8px; margin-top: 10px; font-size: 15px; }
    button { margin-top: 16px; padding: 12px 20px; border: none; border-radius: 8px; background: #e50914; color: white; cursor: pointer; font-size: 17px; transition: .3s; }
    button:hover { background: #b0060f; transform: scale(1.05); }
    #result { margin-top: 20px; font-size: 15px; }
    a { color: #42f5da; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="box">
    <h1>🎥 محمّل يوتيوب</h1>
    <p>ألصق رابط الفيديو واختر الجودة</p>
    <input type="text" id="url" placeholder="https://youtube.com/..." />
    <select id="quality">
      <option value="high">📺 أعلى جودة</option>
      <option value="720p">HD 720p</option>
      <option value="360p">SD 360p</option>
      <option value="audio">🎵 صوت MP3</option>
    </select>
    <button onclick="downloadVideo()">تحميل</button>
    <div id="result"></div>
  </div>

  <script>
    async function downloadVideo() {
      const url = document.getElementById('url').value;
      const quality = document.getElementById('quality').value;
      if(!url) return alert("❌ أدخل رابط صحيح");
      document.getElementById('result').innerHTML = "⏳ جاري التحميل...";
      try {
        const res = await fetch(`/download?url=${encodeURIComponent(url)}&quality=${quality}`);
        const data = await res.json();
        if(data.success){
          document.getElementById('result').innerHTML = `✅ <a href="${data.file}" target="_blank">اضغط هنا للتحميل</a>`;
        } else {
          document.getElementById('result').innerHTML = "⚠️ " + data.error;
        }
      } catch(err){
        document.getElementById('result').innerHTML = "⚠️ تعذر الاتصال بالخادم";
      }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/download")
def download():
    url = request.args.get("url")
    quality = request.args.get("quality", "high")
    if not url:
        return jsonify({"success": False, "error": "missing url"})

    try:
        yt = YouTube(url)
        stream = None

        if quality == "audio":
            stream = yt.streams.filter(only_audio=True).first()
        elif quality == "720p":
            stream = yt.streams.filter(res="720p", progressive=True).first()
        elif quality == "360p":
            stream = yt.streams.filter(res="360p", progressive=True).first()
        else:  # high
            stream = yt.streams.get_highest_resolution()

        if not stream:
            return jsonify({"success": False, "error": "الجودة غير متوفرة"})

        os.makedirs("downloads", exist_ok=True)
        filename = stream.download(output_path="downloads")

        # لو اختار صوت فقط، نحول الامتداد إلى mp3 (باسم فقط، بدون تحويل فعلي)
        if quality == "audio":
            base, ext = os.path.splitext(filename)
            new_file = base + ".mp3"
            os.rename(filename, new_file)
            filename = new_file

        file_url = f"/file/{os.path.basename(filename)}"
        return jsonify({"success": True, "file": file_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/file/<path:name>")
def serve_file(name):
    return send_file(os.path.join("downloads", name), as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
