"""ACEest Fitness and Gym web service.

The course supplied desktop versions of this application. This module keeps
the same programs and calorie rules and exposes them over HTTP so the
CI/CD pipeline can test, containerize, and deploy the service.
"""

import json
import os

from flask import Flask, jsonify, request

APP_VERSION = os.environ.get("APP_VERSION", "3.2.4")

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": (
            "Mon: Back Squat 5x5 + Core\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: Deadlift + Box Jumps\n"
            "Fri: Zone 2 Cardio 30min"
        ),
        "diet": (
            "Breakfast: Egg Whites + Oats\n"
            "Lunch: Grilled Chicken + Brown Rice\n"
            "Dinner: Fish Curry + Millet Roti\n"
            "Target: ~2000 kcal"
        ),
        "calorie_factor": 22,
    },
    "Muscle Gain (MG)": {
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "Breakfast: Eggs + Peanut Butter Oats\n"
            "Lunch: Chicken Biryani\n"
            "Dinner: Mutton Curry + Rice\n"
            "Target: ~3200 kcal"
        ),
        "calorie_factor": 35,
    },
    "Beginner (BG)": {
        "workout": (
            "Full Body Circuit:\n"
            "- Air Squats\n"
            "- Ring Rows\n"
            "- Push-ups\n"
            "Focus: Technique & Consistency"
        ),
        "diet": (
            "Balanced Tamil Meals\n"
            "Idli / Dosa / Rice + Dal\n"
            "Protein Target: 120g/day"
        ),
        "calorie_factor": 26,
    },
}

HOME_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ACEest Fitness</title>
  <style>
    body { font-family: Georgia, serif; margin: 0; background: #f4f1ea; color: #1d283b; }
    header { background: #1a365d; color: #fff; padding: 28px 8vw; }
    header p { margin: 6px 0 0; color: #d6deea; }
    main { padding: 24px 8vw 48px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
    article, form, #result { background: #fff; border: 1px solid #cbd5e1; padding: 16px; }
    h2 { margin-top: 0; color: #1a365d; }
    pre { white-space: pre-wrap; font-family: Consolas, monospace; font-size: 13px; }
    label { display: block; margin-top: 10px; }
    input, select, button { font: inherit; padding: 6px 8px; }
    button { background: #1a365d; color: #fff; border: 0; margin-top: 12px; cursor: pointer; }
    #result { margin-top: 16px; }
  </style>
</head>
<body>
  <header>
    <h1>ACEest Fitness and Gym</h1>
    <p>Version __VERSION__</p>
  </header>
  <main>
    <div class="grid">__CARDS__</div>
    <h2>Calorie target</h2>
    <form id="calc">
      <label>Program
        <select name="program" id="program"></select>
      </label>
      <label>Weight (kg)
        <input name="weight" id="weight" type="number" min="1" step="0.1" value="70">
      </label>
      <button type="submit">Calculate</button>
    </form>
    <div id="result"></div>
  </main>
  <script>
    const programs = __PROGRAMS__;
    const select = document.getElementById("program");
    Object.keys(programs).forEach(function (name) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      select.appendChild(option);
    });
    document.getElementById("calc").addEventListener("submit", function (event) {
      event.preventDefault();
      const program = document.getElementById("program").value;
      const weight = document.getElementById("weight").value;
      fetch("/calories?program=" + encodeURIComponent(program) + "&weight=" + encodeURIComponent(weight))
        .then(function (response) { return response.json().then(function (body) { return { ok: response.ok, body: body }; }); })
        .then(function (result) {
          const node = document.getElementById("result");
          node.textContent = result.ok
            ? result.body.calories + " kcal for " + result.body.program
            : result.body.error;
        });
    });
  </script>
</body>
</html>
"""


def calories_for(weight, program):
    """Daily calorie target used by every supplied desktop version."""
    if program not in PROGRAMS:
        raise KeyError(program)
    weight = float(weight)
    if weight <= 0:
        raise ValueError("weight must be positive")
    return int(round(weight * PROGRAMS[program]["calorie_factor"]))


def create_app(store=None):
    app = Flask(__name__)
    members = {} if store is None else store

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="aceest-fitness", version=APP_VERSION)

    @app.get("/version")
    def version():
        return jsonify(name="ACEest Fitness", version=APP_VERSION)

    @app.get("/")
    def home():
        cards = []
        for name, info in PROGRAMS.items():
            cards.append(
                "<article><h2>{name}</h2><p>Calorie factor {factor}</p>"
                "<pre>{workout}</pre><pre>{diet}</pre></article>".format(
                    name=name,
                    factor=info["calorie_factor"],
                    workout=info["workout"],
                    diet=info["diet"],
                )
            )
        page = (
            HOME_PAGE.replace("__VERSION__", APP_VERSION)
            .replace("__CARDS__", "".join(cards))
            .replace("__PROGRAMS__", json.dumps(PROGRAMS))
        )
        return page

    @app.get("/programs")
    def programs():
        return jsonify(programs=PROGRAMS)

    @app.get("/calories")
    def calories():
        program = request.args.get("program", "")
        weight = request.args.get("weight", "")
        try:
            value = calories_for(weight, program)
        except KeyError:
            return jsonify(error="unknown program"), 400
        except (TypeError, ValueError):
            return jsonify(error="weight must be a positive number"), 400
        return jsonify(program=program, weight=float(weight), calories=value)

    @app.post("/members")
    def add_member():
        data = request.get_json(silent=True) or {}
        name = str(data.get("name") or "").strip()
        program = data.get("program")
        if not name:
            return jsonify(error="name is required"), 400
        if name in members:
            return jsonify(error="member already exists"), 409
        if program not in PROGRAMS:
            return jsonify(error="unknown program"), 400
        try:
            age = int(data.get("age"))
            weight = float(data.get("weight"))
            adherence = int(data.get("adherence", 0))
        except (TypeError, ValueError):
            return jsonify(error="age, weight, and adherence must be numbers"), 400
        if age < 16 or age > 80 or weight <= 0:
            return jsonify(error="age must be 16-80 and weight must be positive"), 400
        if adherence < 0 or adherence > 100:
            return jsonify(error="adherence must be 0-100"), 400
        member = {
            "name": name,
            "age": age,
            "weight": weight,
            "program": program,
            "calories": calories_for(weight, program),
            "adherence": adherence,
            "notes": str(data.get("notes") or "").strip(),
            "progress": [],
        }
        members[name] = member
        return jsonify(member), 201

    @app.get("/members")
    def list_members():
        return jsonify(members=list(members.values()))

    @app.get("/members/<name>")
    def get_member(name):
        member = members.get(name)
        if member is None:
            return jsonify(error="member not found"), 404
        return jsonify(member)

    @app.post("/members/<name>/progress")
    def add_progress(name):
        member = members.get(name)
        if member is None:
            return jsonify(error="member not found"), 404
        data = request.get_json(silent=True) or {}
        try:
            week = int(data.get("week"))
            adherence = int(data.get("adherence"))
        except (TypeError, ValueError):
            return jsonify(error="week and adherence must be numbers"), 400
        if week < 1 or adherence < 0 or adherence > 100:
            return jsonify(error="invalid week or adherence"), 400
        entry = {"week": week, "adherence": adherence}
        member["progress"].append(entry)
        member["adherence"] = adherence
        return jsonify(entry), 201

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
