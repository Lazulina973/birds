import os, tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

app = Flask(__name__)
CORS(app)
analyzer = Analyzer()

@app.route('/')
def index():
    return 'BIRDS!!!! BirdNET API is running. POST audio to /analyze'

@app.route('/analyze', methods=['POST'])
def analyze():
    audio = request.files.get('audio')
    if not audio:
        return jsonify({'error': 'No audio file'}), 400

    lat      = float(request.form.get('lat')      or 0)
    lon      = float(request.form.get('lon')      or 0)
    min_conf = float(request.form.get('min_conf') or 0.25)
    date_str = request.form.get('date') or ''

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.today()
    except ValueError:
        date = datetime.today()

    suffix = os.path.splitext(audio.filename or '.wav')[1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        audio.save(tmp.name)
        tmp_path = tmp.name

    try:
        rec = Recording(analyzer, tmp_path, lat=lat, lon=lon, date=date, min_conf=min_conf)
        rec.analyze()
        detections = [
            {
                'common_name':     d['common_name'],
                'scientific_name': d['scientific_name'],
                'confidence':      d['confidence'],
                'start_time':      d['start_time'],
                'end_time':        d['end_time'],
            }
            for d in rec.detections
        ]
    finally:
        os.unlink(tmp_path)

    return jsonify({'detections': detections})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
