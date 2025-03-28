#!/usr/bin/env python3

import time
import random
import os
import sys

# Check if Streamlit is installed
try:
    import streamlit as st
except ImportError:
    st = None

# Check if NetworkX and Matplotlib are installed
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba
except ImportError:
    nx = None
    plt = None

from memory_simulator import MemorySimulator, MemoryStatus, MemoryBlock, Generation
from garbage_collector import GarbageCollector, GCAlgorithm

# Fallback console UI if Streamlit is not available
class ConsoleUI:
    def __init__(self):
        self.memory_simulator = MemorySimulator(100)
        self.garbage_collector = GarbageCollector(self.memory_simulator)
        self.running = True

    def display_menu(self):
        """Display the main menu."""
        print("\n" + "=" * 50)
        print("Garbage Collector Simulator")
        print("=" * 50)
        print("1. Allocate Memory")
        print("2. Mark Block as Garbage")
        print("3. Run Garbage Collection")
        print("4. Compact Memory")
        print("5. Show Memory Map")
        print("6. Show Statistics")
        print("7. Change GC Algorithm")
        print("8. Add/Remove Reference")
        print("9. Add/Remove Root")
        print("0. Exit")
        print("=" * 50)

    def display_memory_map(self):
        """Display the memory map in console."""
        blocks = self.memory_simulator.get_all_blocks()
        total_size = self.memory_simulator.total_memory_size

        # Create a memory map representation
        memory_map = [" "] * total_size

        for block in blocks:
            # Use different symbols for different block statuses
            symbol = "#"
            if block.status == MemoryStatus.GARBAGE:
                symbol = "G"
            elif block.status == MemoryStatus.MARKED:
                symbol = "M"

            # Fill the memory map with the block's symbol
            for i in range(block.start_index, block.end_index + 1):
                if 0 <= i < total_size:
                    memory_map[i] = symbol

        # Display the memory map
        print("\nMemory Map (# = Allocated, G = Garbage, M = Marked, _ = Free):")
        print("0" + "_" * 48 + str(total_size))

        # Print memory in rows of 50 blocks
        for i in range(0, total_size, 50):
            row = memory_map[i:min(i+50, total_size)]
            print("".join(row))

        # Print block information
        print("\nBlock Information:")
        for block in blocks:
            gen_str = "Y" if block.generation == Generation.YOUNG else "O"
            print(f"Block {block.id}: Size={block.size}, Status={block.status.name}, "
                  f"Position={block.start_index}-{block.end_index}, Generation={gen_str}")

    def display_statistics(self):
        """Display memory statistics."""
        stats = self.memory_simulator.get_stats()
        print("\nMemory Statistics:")
        print(f"Total Memory: {stats['total_memory']} blocks")
        print(f"Used Memory: {stats['used_memory']} blocks")
        print(f"Free Memory: {stats['free_memory']} blocks")
        print(f"Fragmentation: {stats['fragmentation']}%")
        print(f"GC Algorithm: {self.garbage_collector.get_current_algorithm().name}")

    def allocate_memory(self):
        """Allocate a random amount of memory."""
        size = random.randint(1, 10)
        success, block, error = self.memory_simulator.allocate_memory(size)

        if success:
            print(f"\nAllocated block of size {size} (ID: {block.id})")
        else:
            print(f"\nFailed to allocate memory: {error}")

    def mark_garbage(self):
        """Mark a block as garbage."""
        try:
            block_id = int(input("\nEnter block ID to mark as garbage: "))
            if self.memory_simulator.mark_as_garbage(block_id):
                print(f"Block {block_id} marked as garbage")
            else:
                print(f"Block {block_id} not found or already garbage")
        except ValueError:
            print("Please enter a valid block ID (integer)")

    def run_gc(self):
        """Run garbage collection."""
        algorithm = self.garbage_collector.get_current_algorithm()
        print(f"\nRunning {algorithm.name} garbage collection...")

        result = self.garbage_collector.run_garbage_collection()

        print(f"GC completed in {result['duration']:.2f} ms")
        print(f"Reclaimed {len(result['reclaimed_blocks'])} blocks ({result['reclaimed_memory']} units)")

    def compact_memory(self):
        """Compact memory to reduce fragmentation."""
        self.memory_simulator.compact_memory()
        print("\nMemory compaction completed")

    def change_algorithm(self):
        """Change the garbage collection algorithm."""
        print("\nSelect GC Algorithm:")
        print("1. Mark and Sweep")
        print("2. Generational GC")
        print("3. Reference Counting")

        try:
            choice = int(input("Enter choice (1-3): "))
            if choice == 1:
                self.garbage_collector.set_algorithm(GCAlgorithm.MARK_SWEEP)
            elif choice == 2:
                self.garbage_collector.set_algorithm(GCAlgorithm.GENERATIONAL)
            elif choice == 3:
                self.garbage_collector.set_algorithm(GCAlgorithm.REFERENCE_COUNTING)
            else:
                print("Invalid choice")
                return

            print(f"Algorithm changed to {self.garbage_collector.get_current_algorithm().name}")
        except ValueError:
            print("Please enter a valid choice (integer)")

    def manage_references(self):
        """Add or remove references between blocks."""
        blocks = self.memory_simulator.get_all_blocks()
        if not blocks:
            print("\nNo blocks available")
            return

        print("\nAvailable blocks:")
        for block in blocks:
            print(f"Block {block.id}: Size={block.size}, References={block.references}")

        print("\n1. Add reference")
        print("2. Remove reference")

        try:
            choice = int(input("Enter choice (1-2): "))

            if choice == 1:
                from_id = int(input("Enter source block ID: "))
                to_id = int(input("Enter target block ID: "))

                if self.memory_simulator.add_reference(from_id, to_id):
                    print(f"Added reference from block {from_id} to block {to_id}")
                else:
                    print("Failed to add reference (invalid block IDs)")

            elif choice == 2:
                from_id = int(input("Enter source block ID: "))
                to_id = int(input("Enter target block ID to remove reference to: "))

                if self.memory_simulator.remove_reference(from_id, to_id):
                    print(f"Removed reference from block {from_id} to block {to_id}")
                else:
                    print("Failed to remove reference (invalid block IDs)")

            else:
                print("Invalid choice")

        except ValueError:
            print("Please enter valid block IDs (integers)")

    def manage_roots(self):
        """Add or remove root blocks."""
        blocks = self.memory_simulator.get_all_blocks()
        if not blocks:
            print("\nNo blocks available")
            return

        print("\nRoot blocks: ", self.garbage_collector.root_blocks)
        print("Available blocks:")
        for block in blocks:
            print(f"Block {block.id}: Size={block.size}")

        print("\n1. Add root")
        print("2. Remove root")

        try:
            choice = int(input("Enter choice (1-2): "))

            if choice == 1:
                block_id = int(input("Enter block ID to add as root: "))

                if self.garbage_collector.add_root(block_id):
                    print(f"Added block {block_id} as root")
                else:
                    print(f"Block {block_id} is already a root")

            elif choice == 2:
                block_id = int(input("Enter root block ID to remove: "))

                if self.garbage_collector.remove_root(block_id):
                    print(f"Removed block {block_id} from roots")
                else:
                    print(f"Block {block_id} is not a root")

            else:
                print("Invalid choice")

        except ValueError:
            print("Please enter a valid block ID (integer)")

    def run(self):
        """Run the console UI."""
        while self.running:
            self.display_menu()

            try:
                choice = input("Enter choice (0-9): ")

                if choice == "1":
                    self.allocate_memory()
                elif choice == "2":
                    self.mark_garbage()
                elif choice == "3":
                    self.run_gc()
                elif choice == "4":
                    self.compact_memory()
                elif choice == "5":
                    self.display_memory_map()
                elif choice == "6":
                    self.display_statistics()
                elif choice == "7":
                    self.change_algorithm()
                elif choice == "8":
                    self.manage_references()
                elif choice == "9":
                    self.manage_roots()
                elif choice == "0":
                    self.running = False
                    print("\nExiting Garbage Collector Simulator")
                else:
                    print("\nInvalid choice. Please try again.")

            except Exception as e:
                print(f"Error: {e}")

# Streamlit UI
def run_streamlit_app():
    # Set page configuration
    st.set_page_config(
        page_title="Garbage Collector Simulator",
        page_icon="🗑️",
        layout="wide",
    )

    # Initialize session state for simulator and garbage collector
    if "memory_simulator" not in st.session_state:
        st.session_state.memory_simulator = MemorySimulator(100)
        st.session_state.garbage_collector = GarbageCollector(st.session_state.memory_simulator)
        st.session_state.last_gc_result = None
        st.session_state.selected_block = None

    # Title and description
    st.title("Garbage Collector Simulator")
    st.markdown("""
    This application demonstrates how garbage collection algorithms work in memory management.
    Experiment with different algorithms and visualize the memory allocation and reclamation process.
    """)

    # Sidebar for controls
    with st.sidebar:
        st.header("Memory Controls")

        # Allocate memory
        col1, col2 = st.columns(2)
        with col1:
            alloc_size = st.number_input("Block size", min_value=1, max_value=20, value=5)
        with col2:
            if st.button("Allocate Memory"):
                success, block, error = st.session_state.memory_simulator.allocate_memory(alloc_size)
                if success:
                    st.success(f"Allocated block of size {alloc_size} (ID: {block.id})")
                else:
                    st.error(f"Failed to allocate memory: {error}")

        # Garbage Collection
        st.header("Garbage Collection")

        # Algorithm selection
        algorithm = st.selectbox(
            "GC Algorithm",
            ["Mark and Sweep", "Generational", "Reference Counting"],
            index=0
        )

        # Map algorithm names to enum
        algo_map = {
            "Mark and Sweep": GCAlgorithm.MARK_SWEEP,
            "Generational": GCAlgorithm.GENERATIONAL,
            "Reference Counting": GCAlgorithm.REFERENCE_COUNTING
        }

        # Update algorithm when changed
        if st.session_state.garbage_collector.get_current_algorithm() != algo_map[algorithm]:
            st.session_state.garbage_collector.set_algorithm(algo_map[algorithm])

        # Run GC button
        if st.button("Run Garbage Collection"):
            st.session_state.last_gc_result = st.session_state.garbage_collector.run_garbage_collection()
            reclaimed = st.session_state.last_gc_result["reclaimed_memory"]
            duration = st.session_state.last_gc_result["duration"]
            st.success(f"GC completed in {duration:.2f} ms. Reclaimed {reclaimed} memory units.")

        # Auto GC settings
        st.subheader("Auto GC Settings")
        auto_gc = st.checkbox("Enable Auto GC", value=st.session_state.garbage_collector.is_auto_gc_enabled())
        threshold = st.slider("GC Threshold (%)", min_value=50, max_value=90, value=st.session_state.garbage_collector.get_threshold())

        # Update auto GC settings
        if auto_gc != st.session_state.garbage_collector.is_auto_gc_enabled():
            st.session_state.garbage_collector.set_auto_gc(auto_gc)

        if threshold != st.session_state.garbage_collector.get_threshold():
            st.session_state.garbage_collector.set_threshold(threshold)

        # Memory utilities
        st.header("Memory Utilities")

        if st.button("Compact Memory"):
            st.session_state.memory_simulator.compact_memory()
            st.success("Memory compaction completed")

        if st.button("Reset Memory"):
            st.session_state.memory_simulator.reset()
            st.session_state.garbage_collector.root_blocks = []
            st.success("Memory reset completed")

    # Main area - split into columns
    col1, col2 = st.columns([2, 1])

    # Left column - Memory visualization
    with col1:
        st.header("Memory Visualization")

        # Get all blocks
        blocks = st.session_state.memory_simulator.get_all_blocks()

        # If networkx is available, show graph visualization
        if nx and plt:
            st.subheader("Memory Graph")
            fig, ax = plt.subplots(figsize=(10, 6))

            # Create a graph
            G = nx.DiGraph()

            # Add nodes for each memory block
            for block in blocks:
                # Set node color based on status and generation
                if block.status == MemoryStatus.GARBAGE:
                    color = "gray"
                elif block.status == MemoryStatus.MARKED:
                    color = "green"
                else:  # ALLOCATED
                    color = block.color

                # Add border for selected block
                border = 3 if block.selected else 1

                # Add node with attributes
                G.add_node(
                    block.id,
                    size=block.size * 100,  # Scale size for visibility
                    color=color,
                    generation=block.generation.value,
                    start=block.start_index,
                    end=block.end_index,
                    border=border
                )

            # Add edges for references
            for block in blocks:
                for ref_id in block.references:
                    if st.session_state.memory_simulator.get_block_by_id(ref_id):
                        G.add_edge(block.id, ref_id)

            # Add root nodes (special invisible nodes that point to roots)
            for i, root_id in enumerate(st.session_state.garbage_collector.root_blocks):
                if st.session_state.memory_simulator.get_block_by_id(root_id):
                    root_node = f"root_{i}"
                    G.add_node(root_node, size=50, color="white", border=0)
                    G.add_edge(root_node, root_id, style="dashed")

            # Create positions - try to position nodes based on their memory location
            pos = {}
            for node in G.nodes():
                if isinstance(node, int):  # Regular memory block
                    block = st.session_state.memory_simulator.get_block_by_id(node)
                    if block:
                        pos[node] = (block.start_index, 0)
                else:  # Root node
                    pos[node] = (random.uniform(0, 100), 1)

            # Use spring layout for the rest
            remaining_pos = nx.spring_layout(G.subgraph([n for n in G.nodes() if n not in pos]), seed=42)
            pos.update(remaining_pos)

            # Draw the graph
            node_sizes = [G.nodes[n].get('size', 300) for n in G.nodes()]
            node_colors = [G.nodes[n].get('color', 'blue') for n in G.nodes()]
            linewidths = [G.nodes[n].get('border', 1) for n in G.nodes()]

            nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                                  linewidths=linewidths, ax=ax)
            nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowstyle='->')
            nx.draw_networkx_labels(G, pos, ax=ax)

            plt.title("Memory Block References")
            ax.set_axis_off()

            # Display the graph
            st.pyplot(fig)

        # Memory block representation
        st.subheader("Memory Blocks")

        # Draw a visual representation of memory
        memory_fig, memory_ax = plt.subplots(figsize=(10, 3))

        # Draw background for total memory
        memory_ax.add_patch(plt.Rectangle((0, 0), 100, 1, color='lightgray'))

        # Draw blocks
        for block in blocks:
            # Determine color based on status
            if block.status == MemoryStatus.GARBAGE:
                color = 'gray'
            elif block.status == MemoryStatus.MARKED:
                color = 'lightgreen'
            else:
                color = block.color

            # Get RGB values from the hex color
            rgba_color = to_rgba(color)

            # Draw the block
            memory_ax.add_patch(plt.Rectangle(
                (block.start_index, 0),
                block.size,
                1,
                color=rgba_color,
                alpha=0.8,
                linewidth=2 if block.selected else 1,
                edgecolor='black'
            ))

            # Add text (ID)
            if block.size >= 3:  # Only add ID if block is big enough
                memory_ax.text(
                    block.start_index + block.size/2,
                    0.5,
                    str(block.id),
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=9
                )

        # Set limits and remove axes
        memory_ax.set_xlim(0, 100)
        memory_ax.set_ylim(0, 1)
        memory_ax.set_axis_off()

        # Display the memory visualization
        st.pyplot(memory_fig)

        # Handle block selection
        st.subheader("Block Operations")

        # Show block selection
        block_options = {f"Block {b.id} (Size: {b.size})": b.id for b in blocks}
        if block_options:
            selected_option = st.selectbox("Select block:", options=list(block_options.keys()))
            selected_id = block_options[selected_option]

            # Get the selected block
            selected_block = st.session_state.memory_simulator.get_block_by_id(selected_id)
            st.session_state.memory_simulator.select_block(selected_id)

            # Display block details
            if selected_block:
                st.session_state.selected_block = selected_block
                st.write(f"Status: {selected_block.status.value}")
                st.write(f"Size: {selected_block.size} units")
                st.write(f"Position: {selected_block.start_index} - {selected_block.end_index}")
                st.write(f"Generation: {selected_block.generation.value}")
                st.write(f"References: {selected_block.references}")

                # Action buttons for the selected block
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if selected_block.status == MemoryStatus.ALLOCATED:
                        if st.button("Mark as Garbage"):
                            st.session_state.memory_simulator.mark_as_garbage(selected_id)

                with col_b:
                    root_status = selected_id in st.session_state.garbage_collector.root_blocks

                    if root_status:
                        if st.button("Remove from Roots"):
                            st.session_state.garbage_collector.remove_root(selected_id)
                    else:
                        if st.button("Add as Root"):
                            st.session_state.garbage_collector.add_root(selected_id)

                with col_c:
                    # Reference management
                    if len(blocks) > 1:
                        ref_options = {f"Block {b.id}": b.id for b in blocks if b.id != selected_id}
                        if ref_options:
                            ref_selection = st.selectbox("Reference to:", options=list(ref_options.keys()))
                            ref_id = ref_options[ref_selection]

                            has_ref = ref_id in selected_block.references

                            col_ref1, col_ref2 = st.columns(2)
                            with col_ref1:
                                if not has_ref:
                                    if st.button("Add Reference"):
                                        st.session_state.memory_simulator.add_reference(selected_id, ref_id)
                            with col_ref2:
                                if has_ref:
                                    if st.button("Remove Reference"):
                                        st.session_state.memory_simulator.remove_reference(selected_id, ref_id)
        else:
            st.info("No memory blocks allocated yet. Use the 'Allocate Memory' button to create some.")

    # Right column - Stats and info
    with col2:
        st.header("Memory Statistics")

        # Get memory stats
        stats = st.session_state.memory_simulator.get_stats()

        # Update GC stats if we have a result
        if st.session_state.last_gc_result:
            stats["last_gc_duration"] = st.session_state.last_gc_result["duration"]
            stats["memory_reclaimed"] = st.session_state.last_gc_result["reclaimed_memory"]

        # Display stats
        st.metric("Total Memory", f"{stats['total_memory']} units")
        st.metric("Used Memory", f"{stats['used_memory']} units",
                 delta=f"{stats['used_memory'] / stats['total_memory'] * 100:.1f}%")
        st.metric("Free Memory", f"{stats['free_memory']} units")
        st.metric("Fragmentation", f"{stats['fragmentation']}%")

        if "last_gc_duration" in stats and stats["last_gc_duration"] > 0:
            st.metric("Last GC Duration", f"{stats['last_gc_duration']:.2f} ms")

        if "memory_reclaimed" in stats and stats["memory_reclaimed"] > 0:
            st.metric("Memory Reclaimed", f"{stats['memory_reclaimed']} units")

        # Algorithm information
        st.subheader("Current Algorithm: " + algorithm)

        if algorithm == "Mark and Sweep":
            st.markdown("""
            **Mark and Sweep** works in two phases:
            1. **Mark Phase**: The GC identifies and marks all objects that are still in use (referenced).
            2. **Sweep Phase**: The GC scans the entire memory and reclaims any objects that are not marked.

            This is a simple but effective algorithm used in many programming languages.
            """)
        elif algorithm == "Generational":
            st.markdown("""
            **Generational GC** divides memory into regions based on object age:
            - **Young Generation**: New objects are allocated here. Most objects die young, so this region is collected frequently.
            - **Old Generation**: Objects that survive multiple young gen collections are promoted here. This region is collected less frequently.

            This approach is more efficient because it focuses collection efforts where they'll have the most impact.
            """)
        elif algorithm == "Reference Counting":
            st.markdown("""
            **Reference Counting** tracks the number of references to each object:
            - When an object's reference count drops to zero, it's immediately collected.
            - Simple to implement but struggles with cyclic references.
            - Used in languages like Python (with cycle detection), Objective-C, and PHP.
            """)

    # Automatically run GC if needed
    if st.session_state.garbage_collector.is_auto_gc_enabled():
        result = st.session_state.garbage_collector.check_and_run_auto_gc()
        if result:
            st.session_state.last_gc_result = result
            st.experimental_rerun()

    # Add a footer
    st.markdown("---")
    st.markdown("Garbage Collector Simulator - A visual tool for understanding memory management")

if __name__ == "__main__":
    # Try to run the Streamlit app if Streamlit is available
    if st:
        run_streamlit_app()
    # Otherwise, fall back to the console UI
    else:
        print("Streamlit not found, falling back to console UI")
        console_ui = ConsoleUI()
        console_ui.run()
