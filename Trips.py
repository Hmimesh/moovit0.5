from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import pandas as pd

gtfs_Files_Lcation = './Data/gtfs_data/gtfs_extracted_data'

# Load calendar once at module level
calendar = pd.read_csv(gtfs_Files_Lcation + '/calendar.txt')
# Make sure dates are ints like 20260104
calendar['start_date'] = calendar['start_date'].astype(int)
calendar['end_date'] = calendar['end_date'].astype(int)

@dataclass
class Stop:
    #Represents a physical stop/station
    stop_id: str
    name: str
    lat: float = 0.0
    lon: float = 0.0
    
    def __hash__(self):
        return hash(self.stop_id)
    
    def __eq__(self, other):
        return isinstance(other, Stop) and self.stop_id == other.stop_id


@dataclass
class Route:
    #Represents a transit route (sequence of stops)
    route_id: str
    name: str
    stops: List[Stop] = field(default_factory=list)

    def __hash__(self):
        return hash(self.route_id)

    def __eq__(self, other):
        return isinstance(other, Route) and self.route_id == other.route_id

    def get_stop_index(self, stop: Stop) -> Optional[int]:
        #Get the index of a stop in this route
        try:
            return self.stops.index(stop)
        except ValueError:
            return None

    def stops_after(self, stop: Stop) -> List[Stop]:
        #Get all stops that come after the given stop on this route
        idx = self.get_stop_index(stop)
        if idx is None:
            return []
        return self.stops[idx + 1:]


@dataclass
class Trip:
    #Represents a specific journey on a route at a specific time
    trip_id: str
    route: Route
    stop_times: Dict[Stop, Tuple[int, int]]  # stop -> (arrival_time, departure_time) in seconds
    headsign: str = ""  # Trip destination/headsign

    def get_arrival_time(self, stop: Stop) -> Optional[int]:
        #Get arrival time at a stop (in seconds since midnight
        if stop in self.stop_times:
            return self.stop_times[stop][0]
        return None
    
    def get_departure_time(self, stop: Stop) -> Optional[int]:
        #Get departure time from a stop (in seconds since midnight
        if stop in self.stop_times:
            return self.stop_times[stop][1]
        return None
    
    def can_board_at(self, stop: Stop, current_time: int) -> bool:
        #Check if we can board this trip at the given stop and time
        dep_time = self.get_departure_time(stop)
        return dep_time is not None and dep_time >= current_time


@dataclass
class Label:
    """Represents the best known way to reach a stop"""
    arrival_time: int  # seconds since midnight
    previous_stop: Optional[Stop] = None
    trip: Optional[Trip] = None
    round: int = 0
    
    def is_better_than(self, other: Optional['Label']) -> bool:
        """Check if this label is better (earlier arrival) than another"""
        if other is None:
            return True
        return self.arrival_time < other.arrival_time


@dataclass
class Journey:
    """Represents a complete journey from origin to destination"""
    origin: Stop
    destination: Stop
    departure_time: int
    arrival_time: int
    legs: List[Tuple[Stop, Stop, Trip]] = field(default_factory=list)  # (from_stop, to_stop, trip)
    
    def add_leg(self, from_stop: Stop, to_stop: Stop, trip: Trip):
        """Add a leg to the journey"""
        self.legs.append((from_stop, to_stop, trip))
    
    def get_duration(self) -> int:
        """Get total journey duration in seconds"""
        return self.arrival_time - self.departure_time
    
    def get_num_transfers(self) -> int:
        """Get number of transfers (number of legs - 1)"""
        return max(0, len(self.legs) - 1)
    
    def __str__(self):
        duration_min = self.get_duration() // 60
        return (f"Journey from {self.origin.name} to {self.destination.name}\n"
                f"  Departure: {self._format_time(self.departure_time)}\n"
                f"  Arrival: {self._format_time(self.arrival_time)}\n"
                f"  Duration: {duration_min} minutes\n"
                f"  Transfers: {self.get_num_transfers()}\n"
                f"  Legs: {len(self.legs)}")
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds since midnight as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================================
# RAPTOR ALGORITHM
# ============================================================================
class RAPTOR:
    """
    Round-based Public Transit Optimized Router
    
    The algorithm works in rounds, where each round represents one more transit leg.
    Round 0: Starting stops
    Round 1: Stops reachable with 1 vehicle
    Round 2: Stops reachable with 1 transfer (2 vehicles)
    etc.
    """
    
    def __init__(self, routes: List[Route], trips: List[Trip]):
        """
        Initialize RAPTOR with routes and trips
        
        Args:
            routes: List of all routes in the network
            trips: List of all trips (scheduled journeys)
        """
        self.routes = routes
        self.trips = trips
        
        # Build index: stop -> routes that serve this stop
        self.routes_at_stop: Dict[Stop, List[Route]] = {}
        self._build_route_index()

        # Build index: route -> trips on this route
        self.trips_on_route: Dict[Route, List[Trip]] = {}
        self._build_trip_index()

    def _build_route_index(self):
        """Build index of which routes serve which stops"""
        for route in self.routes:
            for stop in route.stops:
                if stop not in self.routes_at_stop:
                    self.routes_at_stop[stop] = []
                if route not in self.routes_at_stop[stop]:
                    self.routes_at_stop[stop].append(route)

    def _build_trip_index(self):
        """Build index of which trips run on which routes"""
        for trip in self.trips:
            if trip.route not in self.trips_on_route:
                self.trips_on_route[trip.route] = []
            self.trips_on_route[trip.route].append(trip)

    def find_earliest_trip(self, route: Route, stop: Stop, current_time: int) -> Optional[Trip]:
        """
        Find the earliest trip on a route that we can board at the given stop and time

        Args:
            route: The route to search
            stop: The stop where we want to board
            current_time: The earliest time we can board (seconds since midnight)

        Returns:
            The earliest trip we can board, or None if no trip is available
        """
        if route not in self.trips_on_route:
            return None

        earliest_trip = None
        earliest_departure = float('inf')

        for trip in self.trips_on_route[route]:
            if trip.can_board_at(stop, current_time):
                dep_time = trip.get_departure_time(stop)
                if dep_time < earliest_departure:
                    earliest_departure = dep_time
                    earliest_trip = trip

        return earliest_trip

    def query(self,
              origin: Stop,
              destination: Stop,
              departure_time: int,
              max_rounds: int = 5) -> Optional[Journey]:
        """
        Find the best journey from origin to destination

        Args:
            origin: Starting stop
            destination: Destination stop
            departure_time: Departure time in seconds since midnight
            max_rounds: Maximum number of transfers + 1 (default 5 = up to 4 transfers)

        Returns:
            Best journey found, or None if no journey exists
        """
        # Initialize labels for each round
        # labels[round][stop] = best Label to reach that stop in that round
        labels: List[Dict[Stop, Label]] = [{} for _ in range(max_rounds + 1)]

        # Round 0: Initialize origin
        labels[0][origin] = Label(arrival_time=departure_time, round=0)

        # Marked stops: stops that were improved in the previous round
        marked_stops: Set[Stop] = {origin}

        # Run RAPTOR rounds
        for k in range(1, max_rounds + 1):
            # Copy labels from previous round
            labels[k] = labels[k-1].copy()

            # Queue of routes to explore
            routes_to_explore: Set[Route] = set()

            # Collect all routes serving marked stops
            for stop in marked_stops:
                if stop in self.routes_at_stop:
                    routes_to_explore.update(self.routes_at_stop[stop])

            # Clear marked stops for this round
            marked_stops = set()

            # Explore each route
            for route in routes_to_explore:
                # Find the earliest stop on this route where we can board
                earliest_boarding_stop = None
                earliest_boarding_time = float('inf')

                for stop in route.stops:
                    if stop in labels[k-1]:
                        arrival_at_stop = labels[k-1][stop].arrival_time
                        if arrival_at_stop < earliest_boarding_time:
                            earliest_boarding_time = arrival_at_stop
                            earliest_boarding_stop = stop

                if earliest_boarding_stop is None:
                    continue

                # Find earliest trip we can board
                trip = self.find_earliest_trip(route, earliest_boarding_stop, earliest_boarding_time)

                if trip is None:
                    continue

                # Traverse the trip and update labels for all reachable stops
                boarded = False
                for stop in route.stops:
                    # Check if we can board at this stop
                    if not boarded and stop in labels[k-1]:
                        if trip.can_board_at(stop, labels[k-1][stop].arrival_time):
                            boarded = True
                            boarding_stop = stop

                    # If we're on the trip, update arrival times
                    if boarded:
                        arrival_time = trip.get_arrival_time(stop)
                        if arrival_time is not None:
                            new_label = Label(
                                arrival_time=arrival_time,
                                previous_stop=boarding_stop,
                                trip=trip,
                                round=k
                            )

                            # Update if this is better than current best
                            current_best = labels[k].get(stop)
                            if new_label.is_better_than(current_best):
                                labels[k][stop] = new_label
                                marked_stops.add(stop)

            # Early termination: if destination wasn't improved, we're done
            if destination in labels[k] and destination not in marked_stops:
                break

        # Reconstruct journey
        return self._reconstruct_journey(origin, destination, departure_time, labels, max_rounds)

    def _reconstruct_journey(self,
                            origin: Stop,
                            destination: Stop,
                            departure_time: int,
                            labels: List[Dict[Stop, Label]],
                            max_rounds: int) -> Optional[Journey]:
        """Reconstruct the journey from the labels"""
        # Find the best round that reached the destination
        best_label = None
        best_round = -1

        for k in range(max_rounds + 1):
            if destination in labels[k]:
                label = labels[k][destination]
                if best_label is None or label.is_better_than(best_label):
                    best_label = label
                    best_round = k

        if best_label is None:
            return None  # No journey found

        # Create journey
        journey = Journey(
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=best_label.arrival_time
        )

        # Backtrack to reconstruct legs
        current_stop = destination
        current_round = best_round

        while current_round > 0:
            label = labels[current_round][current_stop]
            if label.previous_stop and label.trip:
                journey.legs.insert(0, (label.previous_stop, current_stop, label.trip))
                current_stop = label.previous_stop
                current_round -= 1
            else:
                break

        return journey


# ============================================================================
# DATA LOADING FROM GTFS
# ============================================================================

class GTFSLoader:
    """Load RAPTOR data structures from GTFS files"""

    def __init__(self, gtfs_path: str, date: int = 20260104, route_type_filter: int = None, route_limit: int = None):
        """
        Initialize loader with path to GTFS directory

        Args:
            gtfs_path: Path to directory containing GTFS .txt files
            date: service date in YYYYMMDD (e.g. 20260104)
            route_type_filter: Only load routes of this type (2=train, 3=bus, etc.)
            route_limit: Maximum number of routes to load (for testing)
        """
        self.date = int(date)
        self.gtfs_path = gtfs_path
        self.route_type_filter = route_type_filter
        self.route_limit = route_limit
        self.stops_df = None
        self.routes_df = None
        self.trips_df = None
        self.stop_times_df = None

    def load_all(self) -> Tuple[List[Stop], List[Route], List[Trip]]:
        """
        Load all GTFS data and convert to RAPTOR structures,
        filtered to services active on self.date.
        """
        print("Loading GTFS data...")

        # ------------------------------------------------------------------
        # 1) Load the core GTFS files ONCE
        # ------------------------------------------------------------------
        print("  Loading routes...")
        self.routes_df = pd.read_csv(f"{self.gtfs_path}/routes.txt")

        # Filter by route type if specified
        if self.route_type_filter is not None:
            route_type_names = {2: "Trains", 3: "Buses", 0: "Trams", 1: "Subway"}
            type_name = route_type_names.get(self.route_type_filter, f"Type {self.route_type_filter}")
            print(f"  Filtering for route type: {type_name} (type={self.route_type_filter})")
            self.routes_df = self.routes_df[self.routes_df['route_type'] == self.route_type_filter]
            print(f"    Found {len(self.routes_df)} routes")

        # Limit routes if specified
        if self.route_limit:
            self.routes_df = self.routes_df.head(self.route_limit)
            print(f"  Limited to {len(self.routes_df)} routes")

        route_ids = self.routes_df['route_id'].tolist()

        print("  Loading trips...")
        self.trips_df = pd.read_csv(f"{self.gtfs_path}/trips.txt")
        self.trips_df = self.trips_df[self.trips_df['route_id'].isin(route_ids)]
        print(f"    Found {len(self.trips_df)} trips")

        trip_ids = self.trips_df['trip_id'].tolist()

        print("  Loading stop_times (this may take a while)...")
        # Load stop_times in chunks to filter early
        chunks = []
        for chunk in pd.read_csv(f"{self.gtfs_path}/stop_times.txt", chunksize=100000):
            filtered = chunk[chunk['trip_id'].isin(trip_ids)]
            if len(filtered) > 0:
                chunks.append(filtered)
            print(f"    Processed {len(chunks) * 100000} rows...", end='\r')
        self.stop_times_df = pd.concat(chunks, ignore_index=True)
        print(f"\n    Found {len(self.stop_times_df)} stop times")

        stop_ids = self.stop_times_df['stop_id'].unique().tolist()

        print("  Loading stops...")
        self.stops_df = pd.read_csv(f"{self.gtfs_path}/stops.txt")
        self.stops_df = self.stops_df[self.stops_df['stop_id'].isin(stop_ids)]
        print(f"    Found {len(self.stops_df)} stops")

        # ------------------------------------------------------------------
        # 2) Filter by calendar for the given date to avoid 10M+ rows
        # ------------------------------------------------------------------
        weekDay = pd.to_datetime(str(self.date)).day_name().lower()  # e.g. 'friday'

        # Series of service_ids active that day
        active_services = calendar[
            (calendar['start_date'] <= self.date) &
            (calendar['end_date'] >= self.date) &
            (calendar[weekDay] == 1)
        ]['service_id'].astype(str)

        # 🔧 FIX 1: use the Series directly, no ['service_id'] on it
        self.trips_df['service_id'] = self.trips_df['service_id'].astype(str)
        self.trips_df = self.trips_df[self.trips_df['service_id'].isin(active_services)]

        print(f"  Trips after service_id filter: {len(self.trips_df)}")

        # Filter stop_times -> only stop_times whose trip_id is in today's trips
        valid_trip_ids = set(self.trips_df['trip_id'])
        self.stop_times_df = self.stop_times_df[self.stop_times_df['trip_id'].isin(valid_trip_ids)]
        print(f"  Stop times after trip_id filter: {len(self.stop_times_df)}")

        # Filter routes -> only routes used by these trips
        valid_route_ids = self.trips_df['route_id'].unique()
        self.routes_df = self.routes_df[self.routes_df['route_id'].isin(valid_route_ids)]
        print(f"  Routes after filter: {len(self.routes_df)}")

        # Filter stops -> only stops that appear in stop_times
        valid_stop_ids = self.stop_times_df['stop_id'].unique()
        self.stops_df = self.stops_df[self.stops_df['stop_id'].isin(valid_stop_ids)]
        print(f"  Stops after filter: {len(self.stops_df)}")

        # ------------------------------------------------------------------
        # 3) Convert to RAPTOR structures
        # ------------------------------------------------------------------
        stops = self._load_stops()
        routes = self._load_routes(stops)
        mega_trips = self._load_trips(routes, stops)

        return stops, routes, mega_trips

    def _load_stops(self) -> List[Stop]:
        """Convert GTFS stops to Stop objects"""
        stops = []
        for _, row in self.stops_df.iterrows():
            stop = Stop(
                stop_id=str(row['stop_id']),
                name=row['stop_name'],
                lat=row.get('stop_lat', 0.0),
                lon=row.get('stop_lon', 0.0)
            )
            stops.append(stop)
        return stops

    def _load_routes(self, stops: List[Stop]) -> List[Route]:
        """Convert GTFS routes to Route objects"""
        stop_lookup = {s.stop_id: s for s in stops}
        routes = []
        for _, route_row in self.routes_df.iterrows():
            route_id = str(route_row['route_id'])

            route_trips = self.trips_df[self.trips_df['route_id'] == route_row['route_id']]
            if len(route_trips) == 0:
                continue

            first_trip_id = route_trips.iloc[0]['trip_id']
            trip_stops = self.stop_times_df[self.stop_times_df['trip_id'] == first_trip_id]
            trip_stops = trip_stops.sort_values('stop_sequence')

            route_stops = []
            for _, stop_time in trip_stops.iterrows():
                stop_id = str(stop_time['stop_id'])
                if stop_id in stop_lookup:
                    route_stops.append(stop_lookup[stop_id])

            if route_stops:
                # Get route name, handling NaN values
                route_name = route_row.get('route_short_name')
                if pd.isna(route_name) or route_name == '':
                    route_name = route_row.get('route_long_name')
                if pd.isna(route_name) or route_name == '':
                    route_name = f"Route {route_id}"

                route = Route(
                    route_id=route_id,
                    name=str(route_name),
                    stops=route_stops
                )
                routes.append(route)

        return routes

    def _load_trips(self, routes: List[Route], stops: List[Stop]) -> List[Trip]:
        """Convert GTFS trips to Trip objects"""
        route_lookup = {r.route_id: r for r in routes}
        stop_lookup = {s.stop_id: s for s in stops}

        trips = []
        for _, trip_row in self.trips_df.iterrows():
            route_id = str(trip_row['route_id'])
            if route_id not in route_lookup:
                continue

            route = route_lookup[route_id]
            trip_id = str(trip_row['trip_id'])

            trip_stop_times = self.stop_times_df[self.stop_times_df['trip_id'] == trip_row['trip_id']]
            if len(trip_stop_times) == 0:
                continue

            stop_times = {}
            for _, st in trip_stop_times.iterrows():
                stop_id = str(st['stop_id'])
                if stop_id in stop_lookup:
                    stop = stop_lookup[stop_id]
                    arrival = self._time_to_seconds(st['arrival_time'])
                    departure = self._time_to_seconds(st['departure_time'])
                    stop_times[stop] = (arrival, departure)

            if stop_times:
                # Get headsign (destination)
                headsign = trip_row.get('trip_headsign', '')
                if pd.isna(headsign):
                    headsign = ''

                trips.append(Trip(
                    trip_id=trip_id,
                    route=route,
                    stop_times=stop_times,
                    headsign=str(headsign)
                ))

        return trips

    @staticmethod
    def _time_to_seconds(time_str: str) -> int:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return hours * 3600 + minutes * 60 + seconds

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Example of how to use the RAPTOR algorithm"""

    # Method 1: Load from GTFS files
    print("=" * 70)
    print("RAPTOR Algorithm - OOP Implementation")
    print("=" * 70)

    # Load data
    loader = GTFSLoader("Data/gtfs_data/gtfs_extracted_data")
    stops, routes, trips = loader.load_all()

    print(f"\nLoaded network:")
    print(f"  {len(stops)} stops")
    print(f"  {len(routes)} routes")
    print(f"  {len(trips)} trips")

    # Create RAPTOR instance
    print("\nInitializing RAPTOR...")
    raptor = RAPTOR(routes, trips)

    # Find a journey
    print("\nSearching for journey...")

    # You need to find the actual Stop objects for your origin/destination
    # For now, let's just show the structure
    origin = stops[0]  # Replace with actual origin
    destination = stops[100]  # Replace with actual destination
    departure_time = 8 * 3600 + 30 * 60  # 08:30:00

    journey = raptor.query(origin, destination, departure_time, max_rounds=5)

    if journey:
        print("\n" + "=" * 70)
        print("JOURNEY FOUND!")
        print("=" * 70)
        print(journey)
        print("\nLegs:")
        for i, (from_stop, to_stop, trip) in enumerate(journey.legs, 1):
            print(f"  {i}. {from_stop.name} → {to_stop.name}")
            print(f"     Trip: {trip.trip_id} on Route: {trip.route.name}")
    else:
        print("\nNo journey found!")

if __name__ == "__main__":
    print("=" * 70)
    print("RAPTOR Algorithm - OOP Implementation")
    print("=" * 70)

    # ----- 1. Ask for date (for filtering GTFS) -----
    default_date = 20260104  # YYYYMMDD
    date_str = input(f"\nEnter date (YYYYMMDD) [default {default_date}]: ").strip()

    if date_str == "":
        date_int = default_date
    else:
        try:
            date_int = int(date_str)
        except ValueError:
            print(f"Invalid date '{date_str}', using default {default_date}")
            date_int = default_date

    # ----- 1.5. Ask for filtering options -----
    print("\n💡 Loading all routes can be VERY SLOW (5-10 minutes)")
    print("   Recommended: Filter by route type or limit routes")
    print("\nOptions:")
    print("  1. Trains only (🚆) - FAST (~30 seconds)")
    print("  2. Buses only (🚌) - SLOW (~3-5 minutes)")
    print("  3. Limit to first 100 routes - MEDIUM")
    print("  4. Load all routes - VERY SLOW (5-10 minutes)")

    choice = input("\nChoose option (1-4) [default 1]: ").strip()

    if choice == "2":
        route_type_filter = 3  # Buses
        route_limit = None
    elif choice == "3":
        route_type_filter = None
        route_limit = 100
    elif choice == "4":
        print("\n⚠️  WARNING: This will take 5-10 minutes!")
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        if confirm == "yes":
            route_type_filter = None
            route_limit = None
        else:
            print("Cancelled. Using trains only.")
            route_type_filter = 2  # Trains
            route_limit = None
    else:  # default to option 1
        route_type_filter = 2  # Trains
        route_limit = None

    # ----- 2. Load data for that date -----
    loader = GTFSLoader("Data/gtfs_data/gtfs_extracted_data", date_int, route_type_filter, route_limit)
    stops, routes, trips = loader.load_all()

    print(f"\n✅ Loaded network for {date_int}:")
    print(f"   {len(stops)} stops")
    print(f"   {len(routes)} routes")
    print(f"   {len(trips)} trips")

    print("\n📍 Sample stops (first 15):")
    for i, stop in enumerate(stops[:15]):
        print(f"   {i+1}. {stop.name}")

    print("\n💡 TIP: You can enter partial stop names (e.g., 'תל אביב' or 'Tel Aviv')")

    # ----- 3. Ask for origin / destination -----
    Start = input("\nEnter start stop: ").strip()
    End = input("Enter end stop: ").strip()

    # ----- 4. Ask for time -----
    time_str = input("Enter time (HH:MM[:SS]) [default 08:30:00]: ").strip()
    if time_str == "":
        time_str = "08:30:00"

    # Parse time safely (support HH:MM or HH:MM:SS)
    parts = time_str.split(":")
    try:
        if len(parts) == 2:
            h, m = parts
            s = "00"
        elif len(parts) == 3:
            h, m, s = parts
        else:
            raise ValueError("Bad time format")

        departure_time = int(h) * 3600 + int(m) * 60 + int(s)
    except ValueError:
        print(f"Invalid time '{time_str}', using default 08:30:00")
        departure_time = 8 * 3600 + 30 * 60

    # ----- 5. Find matching stops -----
    origin = None
    destination = None

    # Case-insensitive partial match
    start_lower = Start.lower()
    end_lower = End.lower()

    for stop in stops:
        stop_name_lower = stop.name.lower()
        if start_lower in stop_name_lower and origin is None:
            origin = stop
        if end_lower in stop_name_lower and destination is None:
            destination = stop

    if origin is None:
        print(f"\n❌ Could not find start stop matching '{Start}'")
        print("\n💡 Available stops (first 20):")
        for i, stop in enumerate(stops[:20]):
            print(f"  {i+1}. {stop.name}")
    elif destination is None:
        print(f"\n❌ Could not find end stop matching '{End}'")
        print("\n💡 Available stops (first 20):")
        for i, stop in enumerate(stops[:20]):
            print(f"  {i+1}. {stop.name}")
    else:
        # ----- 6. Run RAPTOR -----
        print(f"\n🔍 Searching for journey:")
        print(f"   From: {origin.name}")
        print(f"   To: {destination.name}")
        print(f"   Departure: {Journey._format_time(departure_time)}")
        print(f"   Date: {date_int}")

        print("\n⏳ Initializing RAPTOR...")
        raptor = RAPTOR(routes, trips)

        print("⏳ Running query...")
        journey = raptor.query(origin, destination, departure_time, max_rounds=5)

        if journey:
            print("\n" + "=" * 70)
            print("✅ JOURNEY FOUND!")
            print("=" * 70)
            print(journey)
            print("\n" + "=" * 70)
            print("🚌 ROUTE DETAILS:")
            print("=" * 70)

            for i, (from_stop, to_stop, trip) in enumerate(journey.legs, 1):
                arr_time = trip.get_arrival_time(to_stop)
                dep_time = trip.get_departure_time(from_stop)
                duration = (arr_time - dep_time) // 60

                print(f"\n  🚆 Leg {i}: {trip.route.name}")
                if trip.headsign:
                    print(f"     Direction: {trip.headsign}")
                print(f"     Board at: {from_stop.name}")
                print(f"     Depart: {Journey._format_time(dep_time)}")
                print(f"     ↓")
                print(f"     Alight at: {to_stop.name}")
                print(f"     Arrive: {Journey._format_time(arr_time)}")
                print(f"     Duration: {duration} minutes")

                # Show transfer info if not last leg
                if i < len(journey.legs):
                    next_leg = journey.legs[i]
                    next_dep = next_leg[2].get_departure_time(to_stop)
                    if next_dep:
                        wait_time = (next_dep - arr_time) // 60
                        if wait_time > 0:
                            print(f"\n     ⏱️  Transfer time: {wait_time} minutes")

            print("\n" + "=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ No journey found!")
            print("=" * 70)
            print("\n💡 Possible reasons:")
            print("  - No direct connection exists between these stops")
            print("  - No service running at this time on this date")
            print("  - Too many transfers required (try different stops)")
            print(f"  - Check if both stops have routes: ")
            print(f"    {origin.name}: {len(raptor.routes_at_stop.get(origin, []))} routes")
            print(f"    {destination.name}: {len(raptor.routes_at_stop.get(destination, []))} routes")
