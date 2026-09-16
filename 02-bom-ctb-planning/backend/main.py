from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Scenario, ScenarioLine
from .planning import (
    build_component_demand,
    find_where_used,
    get_summary,
    load_bom_rows,
    recalculate_rows,
    save_bom_rows,
    validate_bom,
)
from .schemas import BomSaveRequest, RecalculateRequest, ScenarioSaveRequest

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BOM CTB Scenario Planner")
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/base")
def get_base_plan():
    try:
        rows = build_component_demand()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"rows": rows, "summary": get_summary(rows)}


@app.post("/api/recalculate")
def recalculate(payload: RecalculateRequest):
    rows = recalculate_rows([row.model_dump() for row in payload.rows])
    return {"rows": rows, "summary": get_summary(rows)}


@app.get("/api/bom")
def get_bom():
    rows = load_bom_rows()
    return {"rows": rows, "validation": validate_bom(rows)}


@app.post("/api/bom/validate")
def validate_bom_endpoint(payload: BomSaveRequest):
    return validate_bom([row.model_dump() for row in payload.rows])


@app.post("/api/bom")
def save_bom(payload: BomSaveRequest):
    rows = [row.model_dump() for row in payload.rows]
    result = save_bom_rows(rows)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    return {"message": "BOM saved", "validation": result}


@app.get("/api/where-used/{component}")
def where_used(component: str):
    return find_where_used(component.strip())


@app.post("/api/scenarios")
def save_scenario(payload: ScenarioSaveRequest, db: Session = Depends(get_db)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Scenario name is required")

    scenario = Scenario(name=payload.name.strip(), remark=payload.remark)
    db.add(scenario)
    db.flush()

    for row in payload.rows:
        db.add(
            ScenarioLine(
                scenario_id=scenario.id,
                material=row.material,
                week=row.week,
                demand_qty=row.demand_qty,
                base_supply=row.base_supply,
                scenario_supply=row.scenario_supply,
                projected_balance=row.projected_balance,
                shortage_qty=row.shortage_qty,
                affected_fg=row.affected_fg,
            )
        )

    db.commit()
    return {"id": scenario.id, "name": scenario.name}


@app.get("/api/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
    items = db.query(Scenario).order_by(Scenario.created_at.desc()).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "remark": item.remark,
            "created_at": item.created_at,
        }
        for item in items
    ]


@app.get("/api/scenarios/{scenario_id}")
def load_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    lines = (
        db.query(ScenarioLine)
        .filter(ScenarioLine.scenario_id == scenario_id)
        .order_by(ScenarioLine.material, ScenarioLine.week)
        .all()
    )

    rows = [
        {
            "material": line.material,
            "week": line.week,
            "demand_qty": line.demand_qty,
            "base_supply": line.base_supply,
            "scenario_supply": line.scenario_supply,
            "projected_balance": line.projected_balance,
            "shortage_qty": line.shortage_qty,
            "affected_fg": line.affected_fg or "",
        }
        for line in lines
    ]

    return {
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "remark": scenario.remark,
        },
        "rows": rows,
        "summary": get_summary(rows),
    }
