from flask import Flask, request, jsonify, send_file, render_template_string
from pytube import YouTube
import os

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎞 محمّل يوتيوب</title>
  <style>
    body { font-family: 'Tahoma', sans-serif; background: linear-gradient(135deg,#0f2027,#203a43,#2c5364); color: #fff; text-align: center; }
    .box { margin: 60px auto; max-width: 600px; padding: 25px; background: rgba(0,0,0,0.6); border-radius: 16px; box-shadow: 0 6px 25px rgba(0,0,0,.5); }
    h1 { margin-bottom: 10px; color: #f5c542; }
    input, select, button { width:100%; padding:12px; border:none; border-radius:8px; margin-top:10px; font-size:15px; }
    input, select { background:#21262d; color:#fff; }
    button { background:#e50914; color:white; cursor:pointer; font-weight:bold; font-size:17px; transition:.3s; }
    button:hover { background:#b0060f; transform: scale(1.05); }
    #result { margin-top:20px; font-size:15px; }
    a { color:#42f5da; text-decoration:none; }
    a:hover { text-decoration:underline; }
    img { max-width:100%; border-radius:10px; margin-top:10px; }
  </style>
</head>
<body>
  <div class="box">
    <h1>🎥 محمّل يوتيوب</h1>
    <input type="text" id="url" placeholder="ضع رابط الفيديو هنا ..." />
    <button onclick="getInfo()">جلب المعلومات</button>
    <div id="info"></div>
  </div>

  <script>
    async function getInfo() {
      const url = document.getElementById('url').value;
      if(!url) return alert("❌ أدخل رابط صحيح");
      document.getElementById('info').innerHTML = "⏳ جاري جلب المعلومات...";
      try {
        const res = await fetch("/info?url=" + encodeURIComponent(url));
        const data = await res.json();
        if(data.success){
          let html = `<h3>${data.title}</h3><img src="${data.thumbnail}" alt="thumbnail"><select id="quality">`;
          data.streams.forEach(s => {
            html += `<option value="${s.itag}">${s.resolution} (${s.type})</option>`;
          });
          html += `</select><button onclick="downloadVideo('${url}')">تحميل</button>`;
          document.getElementById('info').innerHTML = html;
        } else {
          document.getElementById('info').innerHTML = "⚠️ لم يتم جلب البيانات";
        }
      } catch(e){
        document.getElementById('info').innerHTML = "⚠️ خطأ بالاتصال";
      }
    }

    async function downloadVideo(url) {
      const itag = document.getElementById('quality').value;
      document.getElementById('info').innerHTML += "<p>⏳ جاري التحميل...</p>";
      const res = await fetch(`/download?url=${encodeURIComponent(url)}&itag=${itag}`);
      const data = await res.json();
      if(data.success){
        document.getElementById('info').innerHTML = `✅ <a href="${data.file}" target="_blank">اضغط هنا للتحميل</a>`;
      } else {
        document.getElementById('info').innerHTML = "⚠️ " + data.error;
      }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/info")
def info():
    url = request.args.get("url")
    if not url:
        return jsonify({"success": False})
    try:
        yt = YouTube(url)
        streams = []
        for s in yt.streams.filter(progressive=True, file_extension='mp4'):
            streams.append({"itag": s.itag, "resolution": s.resolution, "type": "فيديو+صوت"})
        for s in yt.streams.filter(only_audio=True):
            streams.append({"itag": s.itag, "resolution": "صوت فقط", "type": "Audio"})
        return jsonify({"success": True, "title": yt.title, "thumbnail": yt.thumbnail_url, "streams": streams})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/download")
def download():
    url = request.args.get("url")
    itag = request.args.get("itag")
    if not url or not itag:
        return jsonify({"success": False, "error": "missing params"})
    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(int(itag))
        os.makedirs("downloads", exist_ok=True)
        filename = stream.download(output_path="downloads")

        # تحويل الصوت فقط إلى mp3
        if stream.type == "audio":
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
