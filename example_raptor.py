#!/usr/bin/env python3
"""
Simple example of using RAPTOR with Israeli GTFS data.

This script demonstrates how to:
1. Load GTFS data
2. Build a timetable
3. Query routes using RAPTOR
"""

import sys
from pathlib import Path

# Check if pyraptor is installed
try:
    import pyraptor
    print(f"✓ pyraptor is installed (version: {pyraptor.__version__ if hasattr(pyraptor, '__version__') else 'unknown'})")
    print(f"  Location: {pyraptor.__file__}")
except ImportError as e:
    print(f"✗ pyraptor is NOT installed: {e}")
    print("\nPlease install it with: pip install pyraptor")
    sys.exit(1)

# Check if GTFS data exists
gtfs_dir = Path("Data/gtfs_data/gtfs_extracted_data")
if gtfs_dir.exists():
    print(f"\n✓ GTFS data found at: {gtfs_dir}")
    
    # List GTFS files
    gtfs_files = list(gtfs_dir.glob("*.txt"))
    print(f"  Found {len(gtfs_files)} GTFS files:")
    for f in sorted(gtfs_files):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"    - {f.name} ({size_mb:.1f} MB)")
else:
    print(f"\n✗ GTFS data NOT found at: {gtfs_dir}")
    print("\nPlease run: python get_gtfs.py")
    sys.exit(1)

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("""
1. Build the timetable (this may take a while):
   python -m pyraptor.gtfs.timetable -d "20260103" -a "ALL" --icd

2. Query a route (after building timetable):
   python -m pyraptor.query_raptor -or "Tel Aviv" -d "Jerusalem" -t "08:30:00"

3. Or use this Python API:
""")

print("""
from pyraptor import Raptor
from pyraptor.gtfs import load_timetable

# Load the timetable
timetable = load_timetable("path/to/timetable")

# Create RAPTOR instance
raptor = Raptor(timetable)

# Query a route
result = raptor.query(
    origin="Tel Aviv Central",
    destination="Jerusalem Central",
    departure_time="08:30:00"
)

print(result)
""")

print("="*60)

