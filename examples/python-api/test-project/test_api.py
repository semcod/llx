import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import schemas, models, crud

# ---------- Test DB setup ----------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# ---------- Helper data ----------
def sample_order():
    return {
        "customer_name": "Jan Kowalski",
        "table_number": 5,
        "items": [
            {"menu_item_id": 1, "quantity": 2, "special_request": "bez cebuli"},
            {"menu_item_id": 3, "quantity": 1}
        ]
    }

def sample_status_update():
    return {"status": "gotowe"}

# ---------- Unit tests (mocked CRUD) ----------
def test_create_order_unit(monkeypatch):
    from app.routes import orders as order_routes

    async def mock_create_order(db, order_in):
        return models.Order(
            id=1,
            customer_name=order_in.customer_name,
            table_number=order_in.table_number,
            status="nowe",
            items=[models.OrderItem(**item.dict()) for item in order_in.items]
        )

    monkeypatch.setattr(order_routes.crud, "create_order", mock_create_order)

    client = TestClient(app)
    response = client.post("/orders/", json=sample_order())
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == sample_order()["customer_name"]
    assert data["table_number"] == sample_order()["table_number"]
    assert len(data["items"]) == 2

def test_get_order_unit(monkeypatch):
    from app.routes import orders as order_routes

    fake_order = models.Order(
        id=10,
        customer_name="Anna Nowak",
        table_number=2,
        status="w realizacji",
        items=[]
    )

    async def mock_get_order(db, order_id):
        return fake_order if order_id == 10 else None

    monkeypatch.setattr(order_routes.crud, "get_order", mock_get_order)

    client = TestClient(app)
    response = client.get("/orders/10")
    assert response.status_code == 200
    assert response.json()["id"] == 10

    response = client.get("/orders/999")
    assert response.status_code == 404

def test_update_order_status_unit(monkeypatch):
    from app.routes import orders as order_routes

    async def mock_update_order_status(db, order_id, status):
        return models.Order(
            id=order_id,
            customer_name="Test",
            table_number=1,
            status=status,
            items=[]
        )

    monkeypatch.setattr(order_routes.crud, "update_order_status", mock_update_order_status)

    client = TestClient(app)
    response = client.patch("/orders/5/status", json=sample_status_update())
    assert response.status_code == 200
    assert response.json()["status"] == "gotowe"

# ---------- Integration tests (real DB via TestClient) ----------
def test_create_order_integration(client):
    response = client.post("/orders/", json=sample_order())
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["customer_name"] == sample_order()["customer_name"]
    assert data["table_number"] == sample_order()["table_number"]
    assert len(data["items"]) == 2
    # check nested items
    assert data["items"][0]["menu_item_id"] == 1
    assert data["items"][0]["quantity"] == 2

def test_get_order_integration(client):
    # create first
    create_resp = client.post("/orders/", json=sample_order())
    order_id = create_resp.json()["id"]

    # fetch
    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == order_id

    # non‑existent
    not_found = client.get("/orders/0")
    assert not_found.status_code == 404

def test_list_orders_integration(client):
    # create two orders
    client.post("/orders/", json={**sample_order(), "customer_name": "A"})
    client.post("/orders/", json={**sample_order(), "customer_name": "B"})

    list_resp = client.get("/orders/")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2

def test_update_order_status_integration(client):
    create_resp = client.post("/orders/", json=sample_order())
    order_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/orders/{order_id}/status", json=sample_status_update())
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "gotowe"

    # verify persistence
    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.json()["status"] == "gotowe"

def test_delete_order_integration(client):
    create_resp = client.post("/orders/", json=sample_order())
    order_id = create_resp.json()["id"]

    del_resp = client.delete(f"/orders/{order_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 404

# ---------- Validation / error handling ----------
def test_create_order_missing_fields(client):
    # missing customer_name
    payload = {"table_number": 3, "items": []}
    resp = client.post("/orders/", json=payload)
    assert resp.status_code == 422

def test_create_order_invalid_item(client):
    payload = {
        "customer_name": "Test",
        "table_number": 1,
        "items": [{"menu_item_id": "not-an-int", "quantity": 1}]
    }
    resp = client.post("/orders/", json=payload)
    assert resp.status_code == 422

def test_update_status_invalid_transition(client):
    # assuming status can only move forward: nowe -> w realizacji -> gotowe -> zamkniete
    create_resp = client.post("/orders/", json=sample_order())
    order_id = create_resp.json()["id"]

    # try to jump to 'zamkniete' directly    resp = client.patch(f"/orders/{order_id}/status", json={"status": "zamkniete"})
    assert resp.status_code == 400  # business rule violation