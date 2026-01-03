# Israeli Public Transit RAPTOR

This project uses the RAPTOR (Rapid Access to Public Transport Operations Research) algorithm to find optimal routes in Israeli public transportation using real GTFS data from the Israeli Ministry of Transport.

## What is RAPTOR?

RAPTOR is a fast algorithm for finding the best public transit routes. It can:
- Find the **fastest route** from A to B
- Find **multiple good options** within a time window
- Optimize for **multiple criteria** (time, fare, number of transfers)

## Quick Start

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
- `-d` = Date (YYYYMMDD format) - use today's date or a recent date
- `-a` = Agency - use "ALL" for all Israeli operators, or specific operator names
- `--icd` = Include calendar dates

### 5. Query Routes

Once the timetable is built, you can query routes:

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

## Understanding the Algorithms

### RAPTOR
- **What it does:** Finds ONE journey with the earliest arrival time
- **Use when:** You just want the fastest route
- **Example:** "Get me to work as fast as possible"

### Range RAPTOR (rRAPTOR)
- **What it does:** Finds MULTIPLE good journeys across a time window
- **Use when:** You want options to choose from
- **Example:** "Show me all good options between 8-9 AM"

### McRAPTOR
- **What it does:** Finds Pareto-optimal journeys considering time, fare, and transfers
- **Use when:** You want to balance speed, cost, and convenience
- **Example:** "I don't mind a slightly longer trip if it's cheaper or has fewer transfers"

### Range McRAPTOR (rMcRAPTOR)
- **What it does:** Combines both - multiple criteria across a time window
- **Use when:** You want the most comprehensive set of options
- **Example:** "Show me all reasonable options considering time, cost, and transfers"

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

## Common Issues

### "No module named pyraptor.gtfs.timetable"
- Make sure you installed pyraptor: `pip install pyraptor`
- Check installation: `python -c "import pyraptor; print(pyraptor.__file__)"`

### "Can't push to GitHub - files too big"
- The GTFS data files are large and should NOT be committed to git
- They are already in `.gitignore` as `Data/` and `*.zip`
- Only commit your code, not the data

### "Timetable build is slow"
- This is normal! Processing 400MB+ of transit data takes time
- The Israeli GTFS dataset is very large (all operators nationwide)
- Consider using a specific operator with `-a "operator_name"` instead of "ALL"

## References

- [pyraptor GitHub](https://github.com/lmeulen/pyraptor) - The Python RAPTOR implementation
- [Israeli GTFS Data](https://gtfs.mot.gov.il/) - Official government transit data
- [RAPTOR Paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2012/01/raptor_alenex.pdf) - Original algorithm research

## License

MIT
