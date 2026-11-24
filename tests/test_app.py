import ACEest_Fitness
from ACEest_Fitness import calories_for, create_app


def client():
    app = create_app()
    api = app.test_client()
    api.held_app = app
    return api


def test_calorie_factors_match_the_supplied_programs():
    assert calories_for(70, "Fat Loss (FL)") == 1540
    assert calories_for(80, "Muscle Gain (MG)") == 2800
    assert calories_for(60, "Beginner (BG)") == 1560


def test_calories_reject_unknown_program_and_bad_weight():
    api = client()
    unknown = api.get("/calories?program=Yoga&weight=70")
    assert unknown.status_code == 400
    missing = api.get("/calories?program=Beginner%20(BG)&weight=0")
    assert missing.status_code == 400


def test_health_and_version():
    api = client()
    health = api.get("/health")
    assert health.status_code == 200
    assert health.get_json()["status"] == "ok"
    assert health.get_json()["version"] == ACEest_Fitness.APP_VERSION
    version = api.get("/version").get_json()
    assert version["name"] == "ACEest Fitness"


def test_home_lists_programs_and_version():
    page = client().get("/")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "ACEest Fitness" in body
    assert "Fat Loss (FL)" in body
    assert ACEest_Fitness.APP_VERSION in body


def test_programs_endpoint():
    api = client()
    payload = api.get("/programs").get_json()["programs"]
    assert set(payload) == {"Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"}
    assert payload["Muscle Gain (MG)"]["calorie_factor"] == 35


def test_member_is_saved_with_calorie_target():
    api = client()
    created = api.post(
        "/members",
        json={
            "name": "Chaitanya Reddy",
            "age": 24,
            "weight": 70,
            "program": "Fat Loss (FL)",
            "adherence": 80,
            "notes": "2025TM93047",
        },
    )
    assert created.status_code == 201
    body = created.get_json()
    assert body["calories"] == 1540
    listed = api.get("/members").get_json()["members"]
    assert listed[0]["name"] == "Chaitanya Reddy"
    fetched = api.get("/members/Chaitanya Reddy")
    assert fetched.status_code == 200


def test_member_validation():
    api = client()
    assert api.post("/members", json={"name": "  "}).status_code == 400
    first = api.post(
        "/members",
        json={"name": "Asha", "age": 30, "weight": 60, "program": "Beginner (BG)"},
    )
    assert first.status_code == 201
    duplicate = api.post(
        "/members",
        json={"name": "Asha", "age": 30, "weight": 60, "program": "Beginner (BG)"},
    )
    assert duplicate.status_code == 409
    young = api.post(
        "/members",
        json={"name": "Kid", "age": 12, "weight": 40, "program": "Beginner (BG)"},
    )
    assert young.status_code == 400


def test_progress_updates_adherence():
    api = client()
    api.post(
        "/members",
        json={"name": "Ravi", "age": 28, "weight": 75, "program": "Muscle Gain (MG)"},
    )
    saved = api.post("/members/Ravi/progress", json={"week": 1, "adherence": 90})
    assert saved.status_code == 201
    member = api.get("/members/Ravi").get_json()
    assert member["adherence"] == 90
    assert member["progress"] == [{"week": 1, "adherence": 90}]
    missing = api.post("/members/Nobody/progress", json={"week": 1, "adherence": 10})
    assert missing.status_code == 404
    invalid = api.post("/members/Ravi/progress", json={"week": 0, "adherence": 10})
    assert invalid.status_code == 400
