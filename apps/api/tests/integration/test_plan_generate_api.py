import pytest
from unittest.mock import patch


def test_generate_plan_basic(test_client):
    payload = {
        "project_id": "proj_9",
        "project_name": "Demo",
        "goal": "Build a small cabinet"
    }

    mock_price = {
        "material_name": "Plywood 4x8",
        "vendor_name": "Test Vendor",
        "unit": "sheet",
        "price": 100.0,
        "confidence": 0.9,
        "fetched_at": None,
    }

    def price_side(name):
        if name in ("Plywood 4x8", "2x4 Lumber", "Screws", "Nails", "Paint"):
            return {**mock_price, "material_name": name}
        return None

    mock_labor = {"hourly_rate": 120.0}
    mock_shipping = {"estimated_cost": 75.0}

    with patch("routers.plans.pricing_resolver.get_material_price", side_effect=price_side):
        with patch("routers.plans.pricing_resolver.get_labor_rate", return_value=mock_labor):
            with patch("routers.plans.pricing_resolver.estimate_shipping_cost", return_value=mock_shipping):
                res = test_client.post("/plans/generate", json=payload)
                assert res.status_code == 200
                data = res.json()
                assert data["project_name"] == "Demo"
                assert isinstance(data["items"], list) and len(data["items"]) >= 1
                assert data["total"] > 0
                assert data["currency"] == "NIS"

