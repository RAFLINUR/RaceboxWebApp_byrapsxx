from flask import Flask, render_template, request, jsonify
from models import db, Run
import json
import math

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///racebox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ==============================
# UTIL FUNCTIONS
# ==============================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meter
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def calculate_total_distance(route):
    total = 0
    for i in range(1, len(route)):
        lat1, lon1 = route[i - 1]
        lat2, lon2 = route[i]
        total += haversine(lat1, lon1, lat2, lon2)
    return total


def calculate_max_speed(telemetry):
    if not telemetry:
        return 0
    return max(telemetry)


def detect_laps(route, min_distance=300, threshold=10):
    laps = []
    if not route:
        return laps

    start_point = route[0]
    lap_distance = 0

    for i in range(1, len(route)):
        lat1, lon1 = route[i - 1]
        lat2, lon2 = route[i]

        d = haversine(lat1, lon1, lat2, lon2)
        lap_distance += d

        distance_to_start = haversine(lat2, lon2, start_point[0], start_point[1])

        if distance_to_start < threshold and lap_distance > min_distance:
            laps.append(round(lap_distance, 2))
            lap_distance = 0

    return laps


# ==============================
# AI PERFORMANCE ANALYSIS
# ==============================

def analyze_run(max_speed, zero_to_hundred, distance):
    if zero_to_hundred and zero_to_hundred > 12:
        return "Start lambat. Throttle kurang agresif."

    if max_speed < 90:
        return "Top speed rendah. Periksa kondisi mesin."

    if distance < 100:
        return "Run terlalu pendek untuk analisis optimal."

    if max_speed > 180:
        return "Kecepatan tinggi. Pastikan keamanan berkendara."

    return "Performa sangat baik. Akselerasi stabil."


# ==============================
# ROUTES
# ==============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/history")
def history():
    runs = Run.query.order_by(Run.created_at.desc()).all()
    return render_template("history.html", runs=runs)


# ==============================
# API SAVE RUN (VALIDATED VERSION)
# ==============================

@app.route("/api/save_run", methods=["POST"])
def save_run():

    if not request.is_json:
        return jsonify({"error": "Invalid request format"}), 400

    data = request.json

    route_data = data.get("route_data", [])
    telemetry_data = data.get("telemetry_data", [])
    zero_to_hundred = data.get("zero_to_hundred")

    # ==========================
    # VALIDATION
    # ==========================

    if len(route_data) < 2:
        return jsonify({"error": "Route data tidak valid"}), 400

    total_distance = calculate_total_distance(route_data)
    max_speed = calculate_max_speed(telemetry_data)

    # Anti cheat rules
    if max_speed > 300:
        return jsonify({"error": "Speed tidak masuk akal"}), 400

    if total_distance < 10:
        return jsonify({"error": "Distance terlalu kecil"}), 400

    laps = detect_laps(route_data)

    analysis = analyze_run(max_speed, zero_to_hundred, total_distance)

    run = Run(
        max_speed=round(max_speed, 2),
        zero_to_hundred=zero_to_hundred,
        distance=round(total_distance, 2),
        route_data=json.dumps(route_data),
        telemetry_data=json.dumps(telemetry_data),
        lap_data=json.dumps(laps),
        analysis=analysis
    )

    db.session.add(run)
    db.session.commit()

    return jsonify({
        "message": "Run validated & saved",
        "analysis": analysis,
        "laps": laps
    })


# ==============================
# API GET ALL RUNS
# ==============================

@app.route("/api/history")
def api_history():
    runs = Run.query.order_by(Run.created_at.desc()).all()
    return jsonify([run.to_dict() for run in runs])


# ==============================
# API GET SINGLE RUN
# ==============================

@app.route("/api/run/<int:run_id>")
def get_run(run_id):
    run = Run.query.get_or_404(run_id)
    return jsonify(run.to_dict())


# ==============================
# INIT DATABASE
# ==============================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)