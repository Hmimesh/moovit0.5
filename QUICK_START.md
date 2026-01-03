# RAPTOR OOP - Quick Start Guide

## 🚀 Run the Example

```bash
python raptor_oop.py
```

## 📝 Basic Usage

### 1. Create a Simple Network

```python
from trips import Stop, Route, Trip, RAPTOR

# Stops
a = Stop("A", "Stop A")
b = Stop("B", "Stop B")
c = Stop("C", "Stop C")

# Route
route = Route("R1", "Route 1", [a, b, c])

# Trip (times in seconds since midnight)
trip = Trip(
    trip_id="T1",
    route=route,
    stop_times={
        a: (8*3600, 8*3600),        # 08:00
        b: (8*3600+600, 8*3600+600),   # 08:10
        c: (8*3600+1200, 8*3600+1200)  # 08:20
    }
)

# Query
raptor = RAPTOR([route], [trip])
journey = raptor.query(a, c, 8*3600)
print(journey)
```

### 2. Load from GTFS

```python
from raptor_oop import GTFSLoader, RAPTOR

# Load
loader = GTFSLoader("Data/gtfs_data/gtfs_extracted_data")
stops, routes, trips = loader.load_all()

# Query
raptor = RAPTOR(routes, trips)
origin = stops[0]
destination = stops[100]
journey = raptor.query(origin, destination, 8*3600)
```

## 🧩 Core Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Stop` | Physical location | `stop_id`, `name`, `lat`, `lon` |
| `Route` | Sequence of stops | `stops`, `get_stop_index()` |
| `Trip` | Scheduled journey | `stop_times`, `can_board_at()` |
| `RAPTOR` | Main algorithm | `query()` |
| `Journey` | Result | `legs`, `get_duration()`, `get_num_transfers()` |
| `GTFSLoader` | Data loader | `load_all()` |

## ⏰ Time Format

All times are **seconds since midnight**:

```python
# Convert HH:MM:SS to seconds
time = 8*3600 + 30*60 + 0  # 08:30:00 = 30600 seconds

# Convert back
hours = time // 3600
minutes = (time % 3600) // 60
seconds = time % 60
```

## 🔍 Query Parameters

```python
journey = raptor.query(
    origin=stop_a,           # Stop object
    destination=stop_d,      # Stop object
    departure_time=30600,    # Seconds since midnight
    max_rounds=5             # Max transfers + 1
)
```

## 📊 Journey Information

```python
if journey:
    print(f"Duration: {journey.get_duration() // 60} minutes")
    print(f"Transfers: {journey.get_num_transfers()}")
    print(f"Legs: {len(journey.legs)}")
    
    for from_stop, to_stop, trip in journey.legs:
        print(f"{from_stop.name} → {to_stop.name} (Route {trip.route.name})")
```

## 🎯 Common Patterns

### Find Stop by Name

```python
def find_stop(stops, name):
    return next((s for s in stops if name.lower() in s.name.lower()), None)

origin = find_stop(stops, "Tel Aviv")
destination = find_stop(stops, "Jerusalem")
```

### Multiple Queries

```python
raptor = RAPTOR(routes, trips)  # Initialize once

# Query many times
for origin, dest in pairs:
    journey = raptor.query(origin, dest, 8*3600)
    if journey:
        print(f"{origin.name} → {dest.name}: {journey.get_duration()//60} min")
```

### Different Departure Times

```python
times = [7*3600, 8*3600, 9*3600]  # 07:00, 08:00, 09:00

for t in times:
    journey = raptor.query(origin, dest, t)
    if journey:
        print(f"Depart {t//3600:02d}:00 → Arrive {journey.arrival_time//3600:02d}:{(journey.arrival_time%3600)//60:02d}")
```

## 🐛 Debugging

### Check if stops are in network

```python
print(f"Routes at origin: {len(raptor.routes_at_stop.get(origin, []))}")
print(f"Routes at destination: {len(raptor.routes_at_stop.get(destination, []))}")
```

### Check trips on a route

```python
route = routes[0]
print(f"Trips on {route.name}: {len(raptor.trips_on_route.get(route, []))}")
```

### Trace algorithm execution

Add print statements in `raptor_oop.py`:

```python
def query(self, origin, destination, departure_time, max_rounds=5):
    print(f"Searching from {origin.name} to {destination.name}")
    
    for k in range(1, max_rounds + 1):
        print(f"Round {k}: {len(marked_stops)} marked stops")
        # ...
```

## 📚 Next Steps

1. ✅ Run `python raptor_oop.py` to see it work
2. 📖 Read `RAPTOR_OOP_GUIDE.md` for details
3. 🔧 Modify the simple example to test your understanding
4. 📊 Load real GTFS data and query routes
5. 🚀 Extend with features (walking, fares, etc.)

## 💡 Tips

- **Start simple**: Test with 2-3 stops before loading full GTFS
- **Check data**: Make sure stops are connected by routes
- **Time format**: Always use seconds since midnight
- **Max rounds**: 5 rounds = up to 4 transfers (usually enough)
- **Performance**: Loading GTFS is slow, but querying is fast

## 🎓 Understanding Rounds

```
Round 0: At origin
Round 1: Stops reachable with 1 vehicle (0 transfers)
Round 2: Stops reachable with 2 vehicles (1 transfer)
Round 3: Stops reachable with 3 vehicles (2 transfers)
...
```

Example:
```
A → B → C (Route 1)
    B → D (Route 2)

Query: A to D
Round 1: Reach B, C (via Route 1)
Round 2: Reach D (via Route 2, transfer at B)
```

---

**Happy coding! 🚌🚆**

