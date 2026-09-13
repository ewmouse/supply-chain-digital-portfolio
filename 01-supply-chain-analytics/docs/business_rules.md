# Business Rules

## Inventory Health

### Available Inventory
Available Inventory = On Hand - Blocked Inventory

### Demand Signal
Demand Signal = max(Current Forecast, 4-Week Average Consumption)

### Lead-Time Demand
Lead-Time Demand = Demand Signal × Ceiling(Lead Time Days / 7)

### Confirmed Shortage
Backorder Qty > 0

### Shortage Risk
Available Inventory < Lead-Time Demand

### Excess Candidate
Coverage Weeks >= 12

12 weeks is a configurable demonstration threshold rather than a universal business rule.

## Supplier Performance

### On Time
Receipt Date <= Promised Date

### In Full
Received Qty >= Ordered Qty

### OTIF
Both On Time and In Full

### Fill Rate
min(Received Qty, Ordered Qty) / Ordered Qty