import os
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import (create_engine, String, Integer, Float, DateTime, JSON, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker)

# Override via DATABASE_URL in your .env file for a different local setup.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/grip_solve")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -- ORM --
class Base(DeclarativeBase):
    pass

class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    influences: Mapped[dict] = mapped_column(JSON, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items: Mapped[list["GeneratedItem"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    solve_runs: Mapped[list["SolveRun"]] = relationship(back_populates="generation_run")

class GeneratedItem(Base):
    __tablename__ = "generated_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(128), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    run: Mapped["GenerationRun"] = relationship(back_populates="items")

class SolveRun(Base):
    __tablename__ = "solve_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generation_runs.id"), nullable=False, index=True)
    constraints: Mapped[dict] = mapped_column(JSON, nullable=False)
    objective_param: Mapped[str] = mapped_column(String(64), nullable=False)
    objective_sense: Mapped[str] = mapped_column(String(16), nullable=False)
    objective_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    generation_run: Mapped["GenerationRun"] = relationship(back_populates="solve_runs")
    selections: Mapped[list["SolveSelection"]] = relationship(back_populates="solve_run", cascade="all, delete-orphan")

class SolveSelection(Base):
    __tablename__ = "solve_selections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    solve_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("solve_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("generated_items.id", ondelete="CASCADE"), nullable=False, index=True)
    item: Mapped["GeneratedItem"] = relationship()
    solve_run: Mapped["SolveRun"] = relationship(back_populates="selections")


def init_db():
    Base.metadata.create_all(bind=engine)


# -- SQL Validation Helpers --
_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_ ]{0,62}")

def validate_table_name(name: str) -> str:
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid table name: {name!r}")
    return name

def validate_column_name(name: str) -> str:
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid column name: {name!r}")
    return name

def build_filter_where_clause(filter_model: dict) -> tuple[str, dict]:
    where_clauses: list[str] = []
    params: dict[str, object] = {}

    for idx, (raw_column, details) in enumerate(filter_model.items()):
        if not isinstance(details, dict):
            continue

        column = validate_column_name(raw_column)
        filter_type = details.get("filterType")
        operator = details.get("type", "equals")
        param_name = f"filter_{idx}"

        if filter_type == "text":
            value = details.get("filter", "")
            op_map = {
                "contains":    (f'"{column}" ILIKE :{param_name}', f"%{value}%"),
                "notContains": (f'"{column}" NOT ILIKE :{param_name}', f"%{value}%"),
                "startsWith":  (f'"{column}" ILIKE :{param_name}', f"{value}%"),
                "endsWith":    (f'"{column}" ILIKE :{param_name}', f"%{value}"),
            }
            clause, param_val = op_map.get(operator,(f'"{column}" ILIKE :{param_name}', str(value)))
            where_clauses.append(clause)
            params[param_name] = param_val

        elif filter_type == "number":
            value = details.get("filter")
            if value is None:
                continue

            if operator == "inRange":
                value_to = details.get("filterTo")
                if value_to is None:
                    continue
                param_to = f"filter_{idx}_to"
                where_clauses.append(f'"{column}" >= :{param_name} AND "{column}" <= :{param_to}')
                params[param_name] = value
                params[param_to] = value_to
            else:
                sql_op = {
                    "equals": "=", "notEqual": "!=",
                    "greaterThan": ">", "greaterThanOrEqual": ">=",
                    "lessThan": "<", "lessThanOrEqual": "<=",
                }.get(operator, "=")
                where_clauses.append(f'"{column}" {sql_op} :{param_name}')
                params[param_name] = value

    if not where_clauses:
        return "", params
    return f"WHERE {' AND '.join(where_clauses)}", params
