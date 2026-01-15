# Israeli Public Transit RAPTOR (Hackathon Project)

This repository is a **17-hour hackathon experiment**. We set out to build a route planner for Israeli public transit using real GTFS data, but we **did not finish a working solution**. What we did gain was a crash course in transit routing algorithms and a better understanding of RAPTOR.

## What actually happened

- **Hours 0–4:** We tried to implement **A\*** from scratch. It didn’t work for us (we struggled with modeling transit schedules and transfers correctly).
- **Hours 4–17:** We researched alternatives and found **RAPTOR**. We then tried to wire it up to Israeli GTFS data and see meaningful results, but we didn’t get to a fully working end-to-end route planner in time.

So: this project is **incomplete**, but it captures what we explored and learned during the hackathon.

## What is RAPTOR?

RAPTOR (Rapid Access to Public Transport Operations Research) is a public transit routing algorithm that works on stop times instead of graph edges. In theory, it can:
- Find the **fastest route** from A to B
- Find **multiple good options** within a time window
- Optimize for **multiple criteria** (time, fare, number of transfers)

## What you’ll find in this repo

- Scripts to **download Israeli GTFS data**
- Example commands to **experiment with pyraptor**
- Notes that reflect our attempt to get RAPTOR working during the hackathon

⚠️ **Important:** This repo is not a polished project. Expect rough edges, missing pieces, and broken flows.

## Quick Start (If You Want to Explore)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Israeli GTFS Data

```bash
python get_gtfs.py
```

This downloads ~130MB of Israeli public transportation data from the government API.

### 3. Check Installation

```bash
python example_raptor.py
```

This verifies that pyraptor is installed and GTFS data is available.

### 4. Build the Timetable

**Important:** This step processes the GTFS data into an optimized format for RAPTOR queries. It may take several minutes.

```bash
python -m pyraptor.gtfs.timetable -d "20260103" -a "ALL" --icd
```

**Parameters:**
- `-d` = Date (YYYYMMDD format) - use today’s date or a recent date
- `-a` = Agency - use "ALL" for all Israeli operators, or specific operator names
- `--icd` = Include calendar dates

### 5. Query Routes (If You Get This Far)

Once the timetable is built, you can try queries like:

#### Simple Query (Single Best Route)
```bash
python -m pyraptor.query_raptor -or "Tel Aviv" -d "Jerusalem" -t "08:30:00"
```

#### Range Query (Multiple Options)
```bash
python -m pyraptor.query_range_raptor -or "Tel Aviv" -d "Jerusalem" -st "08:00:00" -et "09:00:00"
```

#### Multi-Criteria Query (Optimize for time, fare, transfers)
```bash
python -m pyraptor.query_mcraptor -or "Tel Aviv" -d "Jerusalem" -t "08:30:00"
```

#### Range Multi-Criteria Query
```bash
python -m pyraptor.query_range_mcraptor -or "Tel Aviv" -d "Jerusalem" -st "08:00:00" -et "09:00:00"
```

## Project Structure

```
.
├── get_gtfs.py           # Downloads Israeli GTFS data
├── example_raptor.py     # Example script to verify installation
├── requirements.txt      # Python dependencies
├── Data/
│   └── gtfs_data/       # Downloaded GTFS data (ignored by git)
└── src/                 # Your custom code goes here
```

## Why this repo exists

We built this during a hackathon to learn, experiment, and try to build something ambitious in a short amount of time. It didn’t become a full product, but it **was valuable as a learning experience**.

If you want a complete and maintained RAPTOR project, check the references below.

## References

- [pyraptor GitHub](https://github.com/lmeulen/pyraptor) - The Python RAPTOR implementation
- [Israeli GTFS Data](https://gtfs.mot.gov.il/) - Official government transit data
- [RAPTOR Paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2012/01/raptor_alenex.pdf) - Original algorithm research

## License

MIT
