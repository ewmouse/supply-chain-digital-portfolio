from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from .database import Base


class Scenario(Base):
    __tablename__ = "scenario"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScenarioLine(Base):
    __tablename__ = "scenario_line"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario.id", ondelete="CASCADE"), index=True)
    material = Column(String(80), nullable=False)
    week = Column(String(20), nullable=False)
    demand_qty = Column(Float, nullable=False)
    base_supply = Column(Float, nullable=False)
    scenario_supply = Column(Float, nullable=False)
    projected_balance = Column(Float, nullable=False)
    shortage_qty = Column(Float, nullable=False)
    affected_fg = Column(String(500), nullable=True)
