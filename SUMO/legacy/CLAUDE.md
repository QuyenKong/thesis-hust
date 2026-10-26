# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SUMO (Simulation of Urban MObility)** traffic simulation project for academic thesis work. It simulates urban traffic scenarios with multiple vehicle types (motorcycles and cars) and analyzes their interactions and behaviors.

### What SUMO Does
SUMO is an open-source traffic simulation suite that:
- Simulates realistic vehicle movement and interactions
- Supports multiple vehicle types with different physics parameters
- Generates statistical outputs about traffic flow, congestion, and vehicle behavior
- Provides GUI visualization and command-line simulation modes

## Project Structure

```
SUMO/
├── routes.rou.xml              # Vehicle type definitions and basic route configuration
├── 2026-10-02-06-34-26/         # Dated simulation output directory
│   ├── osm.sumocfg              # Main SUMO simulation configuration
│   ├── osm.net.xml.gz           # Compressed network topology (roads/intersections)
│   ├── osm.netccfg              # Network configuration
│   ├── osm.motorcycle.trips.xml # Generated motorcycle trip definitions
│   ├── osm.passenger.trips.xml  # Generated passenger car trip definitions
│   ├── osm.poly.xml.gz          # Polygon data (geographic boundaries)
│   ├── output.add.xml           # Additional output definitions
│   ├── osm.view.xml             # GUI view/visualization settings
│   ├── run.bat                  # Script to launch GUI simulation
│   ├── build.bat                # Script to generate traffic scenarios
│   ├── tripinfos.xml            # Output: detailed trip information
│   ├── stats.xml                # Output: simulation statistics
│   └── edgeData.xml             # Output: per-edge traffic data
```

## Common Commands

### Running a Simulation with GUI
```powershell
cd "D:\hust-master\Thesis\SUMO\2026-10-02-06-34-26"
.\run.bat
```
Launches the SUMO GUI (`sumo-gui`) with the configuration in `osm.sumocfg`. This allows interactive visualization of the simulation.

### Generating Traffic Scenarios
```powershell
cd "D:\hust-master\Thesis\SUMO\2026-10-02-06-34-26"
.\build.bat
```
Runs Python scripts using SUMO's `randomTrips.py` tool to generate realistic trip files. This creates:
- `osm.motorcycle.trips.xml` - Motorcycle routes with density 12 vehicles/km
- `osm.passenger.trips.xml` - Passenger car routes with density 8 vehicles/km

### Running Headless (Command-Line) Simulation
```powershell
cd "D:\hust-master\Thesis\SUMO\2026-10-02-06-34-26"
sumo -c osm.sumocfg
```
Runs the simulation without GUI, faster for batch processing and statistics collection.

## Key Configuration Files

### osm.sumocfg (Main Configuration)
Defines the complete simulation:
- **Input**: Network file (`osm.net.xml.gz`) and trip files (motorcycle/passenger)
- **Output**: `tripinfos.xml` (per-vehicle data), `stats.xml` (aggregate statistics)
- **Processing**: Rerouting parameters, traffic light settings
- **Routing**: Vehicle adaptation and re-routing intervals

### routes.rou.xml (Vehicle Types)
Defines vehicle behavior parameters:
- **motorcycle_normal**: Length 1.9m, max speed 16 m/s, accel 2.2 m/s², specific lane change behaviors
- **car_normal**: Length 4.5m, max speed 13 m/s, accel 1.4 m/s², different driving characteristics

### build.bat (Trip Generation)
Uses `randomTrips.py` with these key parameters:
- `--insertion-density`: Vehicles per km (motorcycles: 12, cars: 8)
- `--fringe-factor`: Focus on network edges for realistic route distribution
- `--vehicle-class`: Restrict to motorcycle or passenger only
- `--seed`: Fixed seed (42, 43) for reproducible scenarios
- `--via-edge-types`: Preferred highways (motorway, primary, tertiary links)

## Workflow

**Typical simulation workflow:**
1. Edit vehicle types in `routes.rou.xml` if needed (behavior, speed, dimensions)
2. Run `build.bat` to generate traffic scenarios with desired densities
3. Run `run.bat` to launch GUI and visualize the simulation
4. Analyze output files: `tripinfos.xml` (individual vehicles), `stats.xml` (aggregates)

## Output Files

- **tripinfos.xml**: Contains detailed information about every vehicle trip (departure, arrival, route, speed profile)
- **stats.xml**: Summary statistics (total vehicles, average speed, congestion metrics)
- **edgeData.xml**: Per-road segment statistics (flow, density, occupancy)

These are XML files that can be parsed with standard tools or imported into analysis scripts.

## Dependencies

- **SUMO**: Traffic simulation engine (`sumo-gui` for GUI, `sumo` for headless)
- **Python**: For `randomTrips.py` trip generation (requires `SUMO_HOME` environment variable)
- **.NET Framework**: For batch script execution on Windows

Ensure SUMO is installed and `SUMO_HOME` is set in environment variables before running build/run scripts.

## Key Parameters to Tune

When modifying simulations, consider:
- Vehicle densities (insertion-density in build.bat)
- Vehicle type parameters in routes.rou.xml (speed, acceleration, lane-change aggressiveness)
- Simulation time range (begin/end times in trip generation)
- Rerouting adaptation (frequency and impact in osm.sumocfg)
- Random seed (for reproducibility: always document seed values used)
