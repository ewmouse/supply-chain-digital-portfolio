from collections import defaultdict
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BOM_PATH = DATA_DIR / "bom.csv"


def load_source_data():
    bom = pd.read_csv(BOM_PATH)
    forecast = pd.read_csv(DATA_DIR / "forecast.csv")
    inventory = pd.read_csv(DATA_DIR / "inventory.csv")
    supply = pd.read_csv(DATA_DIR / "supply.csv")
    return bom, forecast, inventory, supply


def load_bom_rows():
    return pd.read_csv(BOM_PATH).to_dict(orient="records")


def normalize_bom_rows(rows):
    cleaned = []
    for row in rows:
        parent = str(row.get("parent", "")).strip()
        component = str(row.get("component", "")).strip()
        if not parent and not component:
            continue
        cleaned.append(
            {
                "parent": parent,
                "component": component,
                "qty_per": float(row.get("qty_per", 0) or 0),
            }
        )
    return cleaned


def validate_bom(rows):
    rows = normalize_bom_rows(rows)
    errors = []

    if not rows:
        return {"valid": False, "errors": ["BOM is empty."]}

    seen = set()
    graph = defaultdict(list)

    for index, row in enumerate(rows, start=1):
        parent = row["parent"]
        component = row["component"]
        qty_per = row["qty_per"]

        if not parent or not component:
            errors.append(f"Row {index}: parent and component are required.")
            continue
        if parent == component:
            errors.append(f"Row {index}: parent and component cannot be the same.")
        if qty_per <= 0:
            errors.append(f"Row {index}: qty_per must be greater than 0.")

        key = (parent, component)
        if key in seen:
            errors.append(f"Duplicate relationship: {parent} -> {component}.")
        seen.add(key)
        graph[parent].append(component)

    state = {}
    path = []
    cycle = None

    def visit(node):
        nonlocal cycle
        if cycle:
            return
        status = state.get(node, 0)
        if status == 1:
            if node in path:
                start = path.index(node)
                cycle = path[start:] + [node]
            return
        if status == 2:
            return

        state[node] = 1
        path.append(node)
        for child in graph.get(node, []):
            visit(child)
        path.pop()
        state[node] = 2

    nodes = set(graph.keys())
    for children in graph.values():
        nodes.update(children)

    for node in nodes:
        if state.get(node, 0) == 0:
            visit(node)
        if cycle:
            break

    if cycle:
        errors.append("BOM cycle detected: " + " -> ".join(cycle))

    return {"valid": len(errors) == 0, "errors": errors}


def save_bom_rows(rows):
    rows = normalize_bom_rows(rows)
    result = validate_bom(rows)
    if not result["valid"]:
        return result

    pd.DataFrame(rows, columns=["parent", "component", "qty_per"]).to_csv(
        BOM_PATH,
        index=False,
    )
    return result


def build_bom_map(bom_df):
    bom_map = defaultdict(list)
    for row in bom_df.itertuples(index=False):
        bom_map[row.parent].append((row.component, float(row.qty_per)))
    return bom_map


def explode_item(item, qty, bom_map, path=None):
    path = path or []
    if item in path:
        raise ValueError("BOM cycle detected during explosion.")

    children = bom_map.get(item, [])
    current_path = path + [item]
    if not children:
        return [(item, qty, current_path)]

    result = []
    for component, qty_per in children:
        result.extend(
            explode_item(component, qty * qty_per, bom_map, current_path)
        )
    return result


def build_reverse_map(bom_df):
    reverse_map = defaultdict(list)
    for row in bom_df.itertuples(index=False):
        reverse_map[row.component].append(row.parent)
    return reverse_map


def find_where_used(component):
    bom, forecast, _, _ = load_source_data()
    reverse_map = build_reverse_map(bom)
    finished_goods = set(forecast["fg"].unique())
    paths = []

    def walk(node, path):
        parents = reverse_map.get(node, [])
        if not parents:
            if node in finished_goods:
                paths.append(path)
            return
        for parent in parents:
            if parent not in path:
                walk(parent, path + [parent])

    walk(component, [component])
    return {
        "component": component,
        "paths": paths,
        "finished_goods": sorted(
            {path[-1] for path in paths if path[-1] in finished_goods}
        ),
    }


def build_component_demand():
    bom, forecast, inventory, supply = load_source_data()
    validation = validate_bom(bom.to_dict(orient="records"))
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    bom_map = build_bom_map(bom)
    demand_rows = []
    impact_map = defaultdict(set)

    for row in forecast.itertuples(index=False):
        exploded = explode_item(row.fg, float(row.demand_qty), bom_map)
        for material, qty, _ in exploded:
            demand_rows.append(
                {"material": material, "week": row.week, "demand_qty": qty}
            )
            impact_map[material].add(row.fg)

    demand = (
        pd.DataFrame(demand_rows)
        .groupby(["material", "week"], as_index=False)["demand_qty"]
        .sum()
    )
    plan = demand.merge(supply, how="left", on=["material", "week"])
    plan["supply_qty"] = plan["supply_qty"].fillna(0)

    inv_map = dict(zip(inventory["material"], inventory["on_hand"]))
    plan["on_hand"] = plan["material"].map(inv_map).fillna(0)
    plan["affected_fg"] = plan["material"].map(
        lambda x: ", ".join(sorted(impact_map.get(x, [])))
    )
    plan = plan.sort_values(["material", "week"]).reset_index(drop=True)

    rows = []
    for material, group in plan.groupby("material", sort=False):
        balance = float(group["on_hand"].iloc[0])
        for row in group.itertuples(index=False):
            supply_qty = float(row.supply_qty)
            demand_qty = float(row.demand_qty)
            balance = balance + supply_qty - demand_qty
            rows.append(
                {
                    "material": material,
                    "week": row.week,
                    "demand_qty": round(demand_qty, 2),
                    "base_supply": round(supply_qty, 2),
                    "scenario_supply": round(supply_qty, 2),
                    "projected_balance": round(balance, 2),
                    "shortage_qty": round(max(-balance, 0), 2),
                    "affected_fg": row.affected_fg,
                }
            )
    return rows


def recalculate_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["material"]].append(row)

    inventory = pd.read_csv(DATA_DIR / "inventory.csv")
    inv_map = dict(zip(inventory["material"], inventory["on_hand"]))
    output = []

    for material, material_rows in grouped.items():
        material_rows = sorted(material_rows, key=lambda x: x["week"])
        balance = float(inv_map.get(material, 0))
        for row in material_rows:
            demand = float(row["demand_qty"])
            supply = float(row["scenario_supply"])
            balance = balance + supply - demand
            updated = dict(row)
            updated["projected_balance"] = round(balance, 2)
            updated["shortage_qty"] = round(max(-balance, 0), 2)
            output.append(updated)

    return sorted(output, key=lambda x: (x["material"], x["week"]))


def get_summary(rows):
    shortage_rows = [row for row in rows if row["shortage_qty"] > 0]
    shortage_materials = {row["material"] for row in shortage_rows}
    first_shortage = None
    if shortage_rows:
        first_shortage = min(shortage_rows, key=lambda x: x["week"])["week"]

    return {
        "materials": len({row["material"] for row in rows}),
        "shortage_materials": len(shortage_materials),
        "first_shortage_week": first_shortage,
        "total_shortage_qty": round(
            sum(row["shortage_qty"] for row in shortage_rows), 2
        ),
    }
