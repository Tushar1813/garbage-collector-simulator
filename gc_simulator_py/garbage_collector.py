#!/usr/bin/env python3

import time
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from memory_simulator import MemorySimulator, MemoryBlock, MemoryStatus, Generation

class GCAlgorithm(Enum):
    MARK_SWEEP = "mark_sweep"
    GENERATIONAL = "generational"
    REFERENCE_COUNTING = "reference_counting"

class GarbageCollector:
    def __init__(self, memory_simulator: MemorySimulator):
        self.memory_simulator = memory_simulator
        self.algorithm = GCAlgorithm.MARK_SWEEP
        self.threshold = 70  # Default: run GC when memory is 70% full
        self.auto_gc = False
        self.root_blocks = []  # IDs of blocks that are considered "roots" (always reachable)
        self.young_gen_max_age = 5  # 5 seconds in the young generation

    def set_algorithm(self, algorithm: GCAlgorithm) -> None:
        """Set the garbage collection algorithm."""
        self.algorithm = algorithm

    def set_threshold(self, threshold: int) -> None:
        """Set the threshold for auto GC (percentage of memory used)."""
        self.threshold = max(1, min(100, threshold))

    def set_auto_gc(self, auto_gc: bool) -> None:
        """Enable or disable automatic garbage collection."""
        self.auto_gc = auto_gc

    def is_auto_gc_enabled(self) -> bool:
        """Check if automatic garbage collection is enabled."""
        return self.auto_gc

    def get_threshold(self) -> int:
        """Get the current GC threshold."""
        return self.threshold

    def get_current_algorithm(self) -> GCAlgorithm:
        """Get the current garbage collection algorithm."""
        return self.algorithm

    def add_root(self, block_id: int) -> bool:
        """Add a block to the root set."""
        if block_id not in self.root_blocks:
            self.root_blocks.append(block_id)
            return True
        return False

    def remove_root(self, block_id: int) -> bool:
        """Remove a block from the root set."""
        if block_id in self.root_blocks:
            self.root_blocks.remove(block_id)
            return True
        return False

    def check_and_run_auto_gc(self) -> Optional[Dict]:
        """Check if GC should run automatically and run it if needed."""
        if not self.auto_gc:
            return None

        stats = self.memory_simulator.get_stats()
        memory_usage_percent = (stats["used_memory"] / stats["total_memory"]) * 100

        if memory_usage_percent >= self.threshold:
            return self.run_garbage_collection()

        return None

    def run_garbage_collection(self) -> Dict:
        """Run the selected garbage collection algorithm."""
        start_time = time.time()
        reclaimed_blocks = []

        if self.algorithm == GCAlgorithm.MARK_SWEEP:
            reclaimed_blocks = self.mark_and_sweep()
        elif self.algorithm == GCAlgorithm.GENERATIONAL:
            reclaimed_blocks = self.generational_gc()
        elif self.algorithm == GCAlgorithm.REFERENCE_COUNTING:
            reclaimed_blocks = self.reference_counting_gc()

        end_time = time.time()
        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        reclaimed_memory = sum(block.size for block in reclaimed_blocks)

        return {
            "reclaimed_blocks": reclaimed_blocks,
            "duration": duration,
            "reclaimed_memory": reclaimed_memory
        }

    def mark_and_sweep(self) -> List[MemoryBlock]:
        """Implement the mark and sweep algorithm."""
        reclaimed_blocks = []
        all_blocks = self.memory_simulator.get_all_blocks()

        # Mark phase: Mark all blocks that are reachable from roots
        if self.root_blocks:
            # If we have explicit roots, use them
            reachable = self._find_reachable_blocks(self.root_blocks)

            # Mark all reachable blocks
            for block in all_blocks:
                if block.id in reachable:
                    self.memory_simulator.mark_block(block.id)
                elif block.status == MemoryStatus.ALLOCATED:
                    # If a block is allocated but not reachable, mark it as garbage
                    block.status = MemoryStatus.GARBAGE
        else:
            # If no roots are defined, mark all allocated blocks
            # (simulating that all are referenced from somewhere)
            for block in all_blocks:
                if block.status == MemoryStatus.ALLOCATED:
                    self.memory_simulator.mark_block(block.id)

        # Sweep phase: Reclaim all garbage blocks
        blocks_copy = all_blocks.copy()  # Copy to avoid modification during iteration
        for block in blocks_copy:
            if block.status == MemoryStatus.GARBAGE:
                if self.memory_simulator.free_block(block.id):
                    reclaimed_blocks.append(block)

        # Reset all marked blocks back to allocated
        for block in self.memory_simulator.get_all_blocks():
            if block.status == MemoryStatus.MARKED:
                block.status = MemoryStatus.ALLOCATED

        return reclaimed_blocks

    def generational_gc(self) -> List[MemoryBlock]:
        """Implement generational garbage collection."""
        reclaimed_blocks = []
        all_blocks = self.memory_simulator.get_all_blocks()
        current_time = time.time()

        # First, promote any young objects that have survived long enough
        for block in all_blocks:
            if (block.generation == Generation.YOUNG and
                block.status == MemoryStatus.ALLOCATED and
                current_time - block.allocation_time > self.young_gen_max_age):
                self.memory_simulator.promote_to_old_generation(block.id)

        # Young generation collection (minor GC) - collect all garbage in young generation
        blocks_copy = all_blocks.copy()
        for block in blocks_copy:
            if (block.generation == Generation.YOUNG and
                block.status == MemoryStatus.GARBAGE):
                if self.memory_simulator.free_block(block.id):
                    reclaimed_blocks.append(block)

        # Occasionally do a full collection (major GC) - 25% chance each time
        should_run_major_gc = (time.time() * 100) % 100 < 25  # Simple deterministic "random"

        if should_run_major_gc:
            blocks_copy = self.memory_simulator.get_all_blocks()
            for block in blocks_copy:
                if (block.generation == Generation.OLD and
                    block.status == MemoryStatus.GARBAGE):
                    if self.memory_simulator.free_block(block.id):
                        reclaimed_blocks.append(block)

        return reclaimed_blocks

    def reference_counting_gc(self) -> List[MemoryBlock]:
        """Implement reference counting garbage collection."""
        reclaimed_blocks = []
        all_blocks = self.memory_simulator.get_all_blocks()

        # Find blocks with no references (excluding roots)
        for block in all_blocks:
            has_references = False

            # Check if this block is referenced by any other block
            for other_block in all_blocks:
                if block.id in other_block.references:
                    has_references = True
                    break

            # Check if it's a root block
            if block.id in self.root_blocks:
                has_references = True

            # If no references and not already marked as garbage, mark it as garbage
            if not has_references and block.status == MemoryStatus.ALLOCATED:
                block.status = MemoryStatus.GARBAGE

        # Reclaim all garbage blocks
        blocks_copy = all_blocks.copy()
        for block in blocks_copy:
            if block.status == MemoryStatus.GARBAGE:
                if self.memory_simulator.free_block(block.id):
                    reclaimed_blocks.append(block)

        return reclaimed_blocks

    def _find_reachable_blocks(self, root_ids: List[int]) -> Set[int]:
        """Find all blocks reachable from the given roots."""
        reachable = set(root_ids)
        queue = root_ids.copy()

        while queue:
            block_id = queue.pop(0)
            block = self.memory_simulator.get_block_by_id(block_id)

            if block:
                for ref_id in block.references:
                    if ref_id not in reachable:
                        reachable.add(ref_id)
                        queue.append(ref_id)

        return reachable
