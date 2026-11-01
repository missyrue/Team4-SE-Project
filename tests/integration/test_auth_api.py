"""INTEGRATION tests - Authentication API + database (TC-Auth-01..03, TC-Sec-01/02/05)."""
from app.models import User

GOOD = {"email": "asha@example.com", "password": "Passw0rdOK", "fullName": "Asha Rao"}


# ------------------------------------------------------------------ TC-Auth-01
def test_TC_Auth_01_register_valid_creates_account(client, db):
    r = client.post("/api/auth/register", json=GOOD)
    assert r.status_code == 201
    assert r.json()["email"] == "asha@example.com"
    assert r.json()["role"] == "customer"
    assert db.query(User).count() == 1


def test_TC_Auth_01_duplicate_email_rejected(client):
    client.post("/api/auth/register", json=GOOD)
    r = client.post("/api/auth/register", json={**GOOD, "email": "ASHA@example.com "})  # same email, different case/space
    assert r.status_code == 409


def test_TC_Auth_01_invalid_email_rejected(client):
    r = client.post("/api/auth/register", json={**GOOD, "email": "not-an-email"})
    assert r.status_code == 400


def test_TC_Auth_01_password_boundary_7_chars_rejected_8_accepted(client):
    assert client.post("/api/auth/register", json={**GOOD, "password": "Abcde12"}).status_code == 400   # 7 chars
    assert client.post("/api/auth/register", json={**GOOD, "password": "Abcdef12"}).status_code == 201  # 8 chars


def test_TC_Auth_01_password_needs_letter_and_digit(client):
    assert client.post("/api/auth/register", json={**GOOD, "password": "onlyletters"}).status_code == 400
    assert client.post("/api/auth/register", json={**GOOD, "password": "12345678"}).status_code == 400


def test_TC_Auth_01_missing_fields_rejected(client):
    assert client.post("/api/auth/register", json={"email": "a@b.com"}).status_code == 400


def test_registering_cannot_create_an_admin(client, db):
    client.post("/api/auth/register", json={**GOOD, "role": "admin"})  # extra field is ignored
    assert db.query(User).one().role == "customer"


# ------------------------------------------------------------------ TC-Auth-02
def test_TC_Auth_02_login_with_valid_credentials(client):
    client.post("/api/auth/register", json=GOOD)
    r = client.post("/api/auth/login", json={"email": GOOD["email"], "password": GOOD["password"]})
    assert r.status_code == 200
    assert r.json()["token"]
    assert r.json()["role"] == "customer"


def test_TC_Auth_02_wrong_password_rejected(client):
    client.post("/api/auth/register", json=GOOD)
    r = client.post("/api/auth/login", json={"email": GOOD["email"], "password": "WrongPass1"})
    assert r.status_code == 401


def test_TC_Auth_02_unknown_email_rejected_with_same_message(client):
    client.post("/api/auth/register", json=GOOD)
    wrong_pw = client.post("/api/auth/login", json={"email": GOOD["email"], "password": "WrongPass1"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "WrongPass1"})
    assert unknown.status_code == 401
    assert unknown.json()["message"] == wrong_pw.json()["message"]  # attacker can't tell which part was wrong


# ------------------------------------------------------------------ TC-Auth-03
def test_TC_Auth_03_logout_ends_session(client):
    client.post("/api/auth/register", json=GOOD)
    token = client.post("/api/auth/login", json={"email": GOOD["email"], "password": GOOD["password"]}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=headers).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401  # protected page needs login again


# ------------------------------------------------------------------ security
def test_TC_Sec_01_protected_endpoint_without_login_is_401(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer made-up-token"}).status_code == 401


def test_TC_Sec_02_database_never_stores_plaintext_password(client, db):
    client.post("/api/auth/register", json=GOOD)
    stored = db.query(User).one().password_hash
    assert GOOD["password"] not in stored


def test_TC_Sec_05_sql_injection_in_login_does_not_log_in(client):
    client.post("/api/auth/register", json=GOOD)
    r = client.post("/api/auth/login", json={"email": "' OR '1'='1", "password": "' OR '1'='1"})
    assert r.status_code == 401


def test_TC_Sec_05_script_in_name_is_stored_as_plain_text_only(client):
    r = client.post("/api/auth/register", json={**GOOD, "fullName": "<script>alert(1)</script>"})
    assert r.status_code == 201
    assert r.json()["fullName"] == "<script>alert(1)</script>"  # returned as JSON data; the UI renders it with textContent
