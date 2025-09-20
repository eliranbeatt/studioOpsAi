from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.trello_service import trello_service


router = APIRouter(prefix="/trello", tags=["trello"])


class PlanCard(BaseModel):
    external_id: Optional[str] = Field(default=None)
    title: str
    description: Optional[str] = Field(default="")
    list_name: Optional[str] = Field(default="To Do")


class PlanExportRequest(BaseModel):
    project_id: str
    project_name: str
    cards: List[PlanCard] = Field(default_factory=list)


@router.post("/export")
def export_plan_to_trello(payload: PlanExportRequest):
    board = trello_service.ensure_board_structure(payload.project_id, payload.project_name)
    if board is None:
        raise HTTPException(status_code=503, detail="Trello not configured")

    board_id = board.get("board_id")
    # Convert cards to plain dicts for service layer
    cards = [c.model_dump() for c in payload.cards]
    result = trello_service.upsert_cards(board_id, cards)

    return {
        "success": result.get("success", False),
        "board": {"id": board_id, "url": board.get("board_url"), "name": board.get("board_name")},
        "summary": {
            "created": result.get("created", 0),
            "updated": result.get("updated", 0),
            "total": result.get("total", 0),
            "errors": result.get("errors", []),
        },
    }

