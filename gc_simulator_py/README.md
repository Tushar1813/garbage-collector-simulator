# Garbage Collector Simulator

A visual simulation tool for understanding memory management and garbage collection algorithms.

## Overview

This application demonstrates how garbage collection works in operating systems and programming languages. It provides an interactive visualization of memory allocation, object references, and garbage collection algorithms.

## Features

- **Memory Allocation**: Allocate memory blocks of different sizes
- **Reference Management**: Create and remove references between objects
- **Multiple GC Algorithms**:
  - **Mark and Sweep**: The classic algorithm that marks reachable objects and sweeps away unreachable ones
  - **Generational GC**: Divides memory into young and old generations for more efficient collection
  - **Reference Counting**: Tracks references to objects and collects them when no references remain
- **Visual Memory Map**: See memory allocation and fragmentation in real-time
- **Object References Graph**: Visualize relationships between objects
- **Memory Statistics**: Track memory usage, fragmentation, and GC performance

## Installation

### Prerequisites

- Python 3.6 or higher
- Optional (for enhanced visualization):
  - NetworkX
  - Matplotlib
  - Streamlit

### Basic Installation

```bash
# Clone the repository (or download the files)
git clone https://github.com/yourusername/gc-simulator.git
cd gc-simulator

# Install the optional dependencies for enhanced visualization
pip install networkx matplotlib streamlit
```

## Usage

### Running with Streamlit (Recommended)

```bash
cd gc_simulator_py
streamlit run app.py
```

This will start a web server and open the application in your browser with a full graphical interface.

### Running in Console Mode

If you don't have Streamlit installed, the application will automatically fall back to console mode:

```bash
cd gc_simulator_py
python app.py
```

## How to Use

1. **Allocate Memory**: Use the "Allocate Memory" button to create new memory blocks
2. **Create References**: Select a block and add references to other blocks
3. **Mark as Garbage**: Dereference blocks you no longer need
4. **Run GC**: Execute the garbage collection algorithm to reclaim unused memory
5. **Change Algorithms**: Switch between different GC algorithms to compare their behavior
6. **Compact Memory**: Reorganize memory blocks to reduce fragmentation

## Educational Value

This simulator helps understand:

- How memory gets allocated and managed
- How garbage collection identifies unused memory
- The differences between various GC algorithms
- The impact of references on object lifetime
- Memory fragmentation and compaction

## Technical Details

The simulator implements three core garbage collection algorithms:

1. **Mark and Sweep**:
   - Mark Phase: Identifies all objects that are still referenced
   - Sweep Phase: Reclaims memory from any objects that weren't marked

2. **Generational GC**:
   - Divides memory into "young" and "old" generations
   - New objects start in the young generation
   - Objects that survive multiple collections are promoted to the old generation
   - Young generation is collected more frequently than the old generation

3. **Reference Counting**:
   - Tracks the number of references to each object
   - When references drop to zero, the object is collected
   - Simple but can't handle circular references without additional mechanisms

## Project Structure

- `memory_simulator.py`: Core memory management functionality
- `garbage_collector.py`: Implementation of GC algorithms
- `app.py`: User interface (Streamlit web UI or console UI)

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues for bugs and feature requests.
