# Multi-Level BOM CTB & Scenario Planning
# 多层 BOM 齐套分析与供需情景规划

A personal supply-chain planning project for multi-level BOM explosion, weekly CTB analysis, shortage tracing and what-if supply scenarios.

个人供应链数字化项目，用于实现多层 BOM 展开、周度物料齐套分析、缺料追溯及供需情景模拟。

> Data used in this project is synthetic and created for portfolio demonstration. No company-sensitive data is included.
>
> 本项目使用模拟数据进行作品集展示，不包含任何实习公司的真实或敏感数据。

---

## Overview / 项目概览

The project focuses on a common manufacturing planning problem: finished-goods demand cannot be compared directly with raw-material supply. Demand must first be translated through the BOM before inventory and future supply can be evaluated.

项目解决制造业计划中的一个基础问题：成品需求不能直接等同于原材料需求，需要先通过多层 BOM 将成品需求逐级展开为零部件需求，再结合库存和未来供应判断物料是否齐套。

![Planning Overview](./docs/screenshots/planning-overview.png)

---

## Business Flow / 业务流程

```text
Finished Goods Forecast
        ↓
Multi-Level BOM
        ↓
BOM Explosion
        ↓
Component Demand
        ↓
On-hand Inventory + Weekly Supply
        ↓
Rolling Projected Balance
        ↓
Shortage Detection
        ↓
Where-used / Affected Finished Goods
        ↓
What-if Supply Scenario
```

---

## Core Features / 核心功能

### 1. Multi-Level BOM Explosion / 多层 BOM 展开

Finished-goods demand is recursively expanded through parent-component relationships until leaf components are reached.

根据 Parent-Component 关系逐层展开成品需求，将 Finished Goods Forecast 转换为底层零部件需求。

### 2. Weekly CTB Analysis / 周度齐套分析

The application combines component demand, on-hand inventory and weekly supply to calculate rolling projected balance and identify shortage timing.

系统结合零部件需求、现有库存和未来供应，按周滚动计算 Projected Balance，并识别首次缺料时间。

```text
Projected Balance(t)
= Projected Balance(t-1)
+ Supply(t)
- Demand(t)
```

### 3. Supply Scenario Planning / 供需情景规划

Users can edit weekly supply quantities or move planned supply between weeks to simulate supply reduction, delay and recovery scenarios.

用户可调整未来供应数量或到货周次，用于模拟供应减少、延迟及恢复情景。

![Supply Scenario](./docs/screenshots/supply-scenario.png)

### 4. BOM Editor & Validation / BOM 编辑与校验

Users can maintain BOM relationships in the browser and validate duplicates, invalid quantities, self-reference and BOM cycles before saving.

支持网页端维护 BOM，并在保存前检查重复关系、异常用量、自引用及循环 BOM。

![BOM Editor and Validation](./docs/screenshots/bom-editor-validation.png)

### 5. Where-used / 反向物料追溯

Components can be traced upward through the BOM to identify affected semi-finished and finished goods.

支持从缺料零部件向上追溯对应半成品和成品，用于判断潜在影响范围。

![Where-used Trace](./docs/screenshots/where-used-trace.png)

---

## Tech Stack / 技术栈

- **Python / Pandas** — BOM explosion, demand transformation and planning calculation
- **PostgreSQL** — scenario persistence
- **SQLAlchemy** — database connection and data persistence
- **FastAPI** — backend API
- **HTML / CSS / JavaScript** — web interface
- **Handsontable** — editable planning and BOM tables
- **Git / GitHub** — version control and project documentation

---

## Data / 数据说明

The project uses synthetic data created for portfolio demonstration.

本项目全部使用模拟数据，仅用于展示供应链计划业务逻辑及数字化实现方式，不包含任何实习公司的真实或敏感数据。

Current input data includes:

- Multi-level BOM
- Finished Goods Forecast
- On-hand Inventory
- Weekly Incoming Supply

```text
data/
├── bom.csv
├── forecast.csv
├── inventory.csv
└── supply.csv
```

---

## Project Structure / 项目结构

```text
02-bom-ctb-planning/
├── backend/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── planning.py
│   └── schemas.py
│
├── data/
│   ├── bom.csv
│   ├── forecast.csv
│   ├── inventory.csv
│   └── supply.csv
│
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── style.css
│
├── docs/
│   └── screenshots/
│       ├── bom-editor-validation.png
│       ├── planning-overview.png
│       ├── supply-scenario.png
│       └── where-used-trace.png
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Run Locally / 本地运行

### 1. Create PostgreSQL Database / 创建数据库

```sql
CREATE DATABASE bom_ctb;
```

### 2. Configure Database Connection / 配置数据库连接

Copy `.env.example` to `.env` and update the PostgreSQL password.

```text
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/bom_ctb
```

### 3. Create Virtual Environment / 创建虚拟环境

```bash
py -3.12 -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies / 安装依赖

```bash
pip install -r requirements.txt
```

### 5. Start FastAPI / 启动项目

```bash
uvicorn backend.main:app --reload
```

Open in browser:

```text
http://127.0.0.1:8000
```

---

## Suggested Demo Flow / 演示流程

1. Review the base Weekly CTB Planning Grid.
2. Identify a material with shortage risk.
3. Move planned supply from one week to another.
4. Recalculate projected balance and shortage timing.
5. Save the supply scenario to PostgreSQL.
6. Open the BOM Editor and review the BOM structure.
7. Run BOM Validation.
8. Use Where-used to trace a component back to affected finished goods.

---

## Current Scope / 当前项目范围

The current version focuses on transparent and explainable material-planning logic.

The current version does not include:

- Production capacity constraints
- MOQ or lot-sizing rules
- Automatic purchase-order generation
- Supplier calendars
- Detailed order-priority allocation
- Machine-learning demand forecasting

当前版本主要用于展示多层 BOM、物料齐套、缺料识别和供需情景规划的核心逻辑，并未尝试模拟完整的 MRP、ERP 或生产计划系统。

---

## Disclaimer / 项目说明

This is a personal portfolio project based on synthetic supply-chain data.

It is not a production system and does not contain confidential data from Michelin, Schneider Electric or any other company.

本项目为个人供应链数字化作品集，使用模拟数据开发，不包含米其林、施耐德电气或其他公司的真实业务数据及敏感信息。