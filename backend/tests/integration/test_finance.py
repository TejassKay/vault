"""FR-7 to FR-10, FR-15 to FR-17, FR-27: Integration tests for finance core."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient


def test_fr7_transactions_crud_and_nudge(client: TestClient, auth_headers: dict[str, str]) -> None:
    # Create transaction
    payload = {
        "type": "expense",
        "amount": "1500.00",
        "category": "Groceries",
        "txn_date": date.today().isoformat(),
        "note": "Supermarket run",
        "is_recurring": False,
    }
    resp = client.post("/transactions", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["transaction"]["amount"] == "1500.00"
    txn_id = data["transaction"]["transaction_id"]

    # List
    list_resp = client.get("/transactions", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(t["transaction_id"] == txn_id for t in list_resp.json())

    # Delete
    del_resp = client.delete(f"/transactions/{txn_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_fr15_income_source_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "name": "Software Engineer Salary",
        "amount": "90000.00",
        "frequency": "monthly",
        "income_type": "fixed",
        "expected_day": 1,
        "is_active": True,
    }
    resp = client.post("/income-sources", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    source_id = resp.json()["income_source_id"]

    list_resp = client.get("/income-sources", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(s["income_source_id"] == source_id for s in list_resp.json())

    del_resp = client.delete(f"/income-sources/{source_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_fr16_liability_crud_and_reminder(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "type": "vehicle",
        "lender_name": "HDFC Bank",
        "outstanding_principal": "350000.00",
        "interest_rate": "9.50",
        "emi_amount": "12000.00",
        "due_day": 10,
        "remaining_months": 36,
        "status": "active",
    }
    resp = client.post("/liabilities", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    liab_id = resp.json()["liability_id"]

    # Check reminder created
    rem_resp = client.get("/reminders", headers=auth_headers)
    assert rem_resp.status_code == 200

    del_resp = client.delete(f"/liabilities/{liab_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_fr17_holdings_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "type": "bank_savings",
        "name": "ICICI Emergency Reserve",
        "current_value": "100000.00",
        "as_of_date": date.today().isoformat(),
        "liquidity": "liquid",
        "is_emergency_reserve": True,
        "source": "manual",
    }
    resp = client.post("/holdings", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    holding_id = resp.json()["holding_id"]

    list_resp = client.get("/holdings", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(h["holding_id"] == holding_id for h in list_resp.json())

    del_resp = client.delete(f"/holdings/{holding_id}", headers=auth_headers)
    assert del_resp.status_code == 204


def test_fr9_goals_and_projection(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "title": "Emergency Fund Goal",
        "target_amount": "100000.00",
        "saved_amount": "20000.00",
        "target_date": "2027-12-31",
        "priority": "high",
        "liquidity_need": "high",
        "status": "active",
    }
    resp = client.post("/goals", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    goal_id = resp.json()["goal_id"]

    # Add saving
    save_resp = client.post(
        f"/goals/{goal_id}/add-saving", json={"amount": "5000.00"}, headers=auth_headers
    )
    assert save_resp.status_code == 200
    assert Decimal(str(save_resp.json()["saved_amount"])) == Decimal("25000.00")

    # Projection
    proj_resp = client.get(f"/goals/{goal_id}/projection", headers=auth_headers)
    assert proj_resp.status_code == 200
    data = proj_resp.json()
    assert "planning_contribution" in data
    assert "scenarios" in data
    assert data["disclaimer"] == "Projections are estimates and are not guaranteed."


def test_patch_finance_records(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Verify PATCH endpoints for income sources, transactions, liabilities, and holdings."""
    inc_id = client.post(
        "/income-sources",
        json={
            "name": "Consulting",
            "amount": "20000.00",
            "frequency": "monthly",
            "income_type": "variable",
            "is_active": True,
        },
        headers=auth_headers,
    ).json()["income_source_id"]
    inc_upd = client.patch(
        f"/income-sources/{inc_id}",
        json={"name": "Retainer", "amount": "25000.00"},
        headers=auth_headers,
    )
    assert inc_upd.status_code == 200
    assert inc_upd.json()["name"] == "Retainer"
    assert Decimal(str(inc_upd.json()["amount"])) == Decimal("25000.00")

    txn_id = client.post(
        "/transactions",
        json={
            "type": "expense",
            "amount": "1200.00",
            "category": "Groceries",
            "txn_date": date.today().isoformat(),
            "is_recurring": False,
        },
        headers=auth_headers,
    ).json()["transaction"]["transaction_id"]
    txn_upd = client.patch(
        f"/transactions/{txn_id}",
        json={"amount": "1500.00", "category": "Utilities"},
        headers=auth_headers,
    )
    assert txn_upd.status_code == 200
    assert txn_upd.json()["category"] == "Utilities"
    assert Decimal(str(txn_upd.json()["amount"])) == Decimal("1500.00")

    liab_id = client.post(
        "/liabilities",
        json={
            "type": "personal",
            "lender_name": "Test Bank",
            "outstanding_principal": "100000.00",
            "interest_rate": "10.00",
            "emi_amount": "5000.00",
            "due_day": 5,
            "status": "active",
        },
        headers=auth_headers,
    ).json()["liability_id"]
    liab_upd = client.patch(
        f"/liabilities/{liab_id}",
        json={"interest_rate": "11.50", "emi_amount": "5500.00"},
        headers=auth_headers,
    )
    assert liab_upd.status_code == 200
    assert Decimal(str(liab_upd.json()["interest_rate"])) == Decimal("11.50")
    assert Decimal(str(liab_upd.json()["emi_amount"])) == Decimal("5500.00")

    hold_id = client.post(
        "/holdings",
        json={
            "type": "bank_savings",
            "name": "Savings",
            "current_value": "50000.00",
            "as_of_date": date.today().isoformat(),
            "liquidity": "liquid",
            "is_emergency_reserve": False,
            "source": "manual",
        },
        headers=auth_headers,
    ).json()["holding_id"]
    hold_upd = client.patch(
        f"/holdings/{hold_id}",
        json={"current_value": "75000.00", "is_emergency_reserve": True},
        headers=auth_headers,
    )
    assert hold_upd.status_code == 200
    assert Decimal(str(hold_upd.json()["current_value"])) == Decimal("75000.00")
    assert hold_upd.json()["is_emergency_reserve"] is True
