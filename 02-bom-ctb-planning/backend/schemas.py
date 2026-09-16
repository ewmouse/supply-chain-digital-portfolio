from typing import List, Optional

from pydantic import BaseModel


class PlanRow(BaseModel):
    material: str
    week: str
    demand_qty: float
    base_supply: float
    scenario_supply: float
    projected_balance: float = 0
    shortage_qty: float = 0
    affected_fg: str = ""


class RecalculateRequest(BaseModel):
    rows: List[PlanRow]


class ScenarioSaveRequest(BaseModel):
    name: str
    remark: Optional[str] = None
    rows: List[PlanRow]


class BomLine(BaseModel):
    parent: str
    component: str
    qty_per: float


class BomSaveRequest(BaseModel):
    rows: List[BomLine]
