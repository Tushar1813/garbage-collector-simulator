#!/usr/bin/env python3

import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

class MemoryStatus(Enum):
    FREE = "free"
    ALLOCATED = "allocated"
    MARKED = "marked"
    GARBAGE = "garbage"

class Generation(Enum):
    YOUNG = "young"
    OLD = "old"

class MemoryBlock:
    def __init__(self, block_id: int, size: int, start_index: int):
        self.id = block_id
        self.size = size
        self.status = MemoryStatus.ALLOCATED
        self.start_index = start_index
        self.end_index = start_index + size - 1
        self.color = self._generate_random_color()
        self.generation = Generation.YOUNG
        self.allocation_time = time.time()
        self.references = []  # IDs of blocks this block references
        self.selected = False

    def _generate_random_color(self) -> str:
        """Generate a random color in hex format."""
        colors = [
            "#FF6B6B", "#4ECDC4", "#FF9F1C", "#3BCEAC", "#6A0572",
            "#4D80E4", "#FF7A5A", "#5D5C61", "#938BA1", "#7AC74F",
            "#F4D35E", "#EE6055", "#60D394", "#AAF683", "#FFD97D"
        ]
        return random.choice(colors)

    def add_reference(self, block_id: int) -> None:
        """Add a reference to another block."""
        if block_id not in self.references:
            self.references.append(block_id)

    def remove_reference(self, block_id: int) -> None:
        """Remove a reference to another block."""
        if block_id in self.references:
            self.references.remove(block_id)

class MemorySimulator:
    def __init__(self, total_size: int = 100):
        self.total_memory_size = total_size
        self.memory_blocks = []  # List of MemoryBlock objects
        self.next_block_id = 1

    def reset(self) -> None:
        """Reset the memory simulation."""
        self.memory_blocks = []
        self.next_block_id = 1

    def allocate_memory(self, size: int) -> Tuple[bool, Optional[MemoryBlock], Optional[str]]:
        """Allocate a new memory block with the given size."""
        if size <= 0:
            return False, None, "Block size must be greater than 0"

        if size > self.total_memory_size:
            return False, None, f"Block size exceeds total memory ({self.total_memory_size})"

        # Check if we have enough free space
        free_memory = self.get_free_memory()
        if size > free_memory:
            return False, None, f"Not enough free memory. Requested {size}, available {free_memory}"

        # Find a suitable position for the new block
        start_index = self._find_free_space_index(size)
        if start_index == -1:
            return False, None, "Memory too fragmented. Try compacting memory or freeing some blocks."

        # Create a new memory block
        new_block = MemoryBlock(self.next_block_id, size, start_index)
        self.next_block_id += 1

        # Insert the block at the correct position
        insert_index = self._find_insert_index(start_index)
        self.memory_blocks.insert(insert_index, new_block)

        return True, new_block, None

    def mark_as_garbage(self, block_id: int) -> bool:
        """Mark a block as garbage (no longer in use)."""
        block = self.get_block_by_id(block_id)
        if block and block.status == MemoryStatus.ALLOCATED:
            block.status = MemoryStatus.GARBAGE
            return True
        return False

    def free_block(self, block_id: int) -> bool:
        """Remove a block from memory."""
        for i, block in enumerate(self.memory_blocks):
            if block.id == block_id:
                self.memory_blocks.pop(i)
                return True
        return False

    def mark_block(self, block_id: int) -> bool:
        """Mark a block as in use."""
        block = self.get_block_by_id(block_id)
        if block and (block.status == MemoryStatus.ALLOCATED or block.status == MemoryStatus.GARBAGE):
            block.status = MemoryStatus.MARKED
            return True
        return False

    def compact_memory(self) -> None:
        """Reorganize memory blocks to eliminate fragmentation."""
        # Sort blocks by start_index
        self.memory_blocks.sort(key=lambda block: block.start_index)

        # Relocate blocks to eliminate fragmentation
        current_index = 0
        for block in self.memory_blocks:
            block.start_index = current_index
            block.end_index = current_index + block.size - 1
            current_index += block.size

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        used_memory = self.get_used_memory()
        free_memory = self.get_free_memory()
        fragmentation = self.calculate_fragmentation()

        return {
            "total_memory": self.total_memory_size,
            "used_memory": used_memory,
            "free_memory": free_memory,
            "fragmentation": fragmentation,
            "last_gc_duration": 0,  # Will be set by GC
            "memory_reclaimed": 0   # Will be set by GC
        }

    def get_all_blocks(self) -> List[MemoryBlock]:
        """Get all memory blocks."""
        return self.memory_blocks.copy()

    def get_block_by_id(self, block_id: int) -> Optional[MemoryBlock]:
        """Get a memory block by its ID."""
        for block in self.memory_blocks:
            if block.id == block_id:
                return block
        return None

    def select_block(self, block_id: int) -> None:
        """Select a block (for UI interactions)."""
        for block in self.memory_blocks:
            block.selected = False

        block = self.get_block_by_id(block_id)
        if block:
            block.selected = True

    def deselect_all_blocks(self) -> None:
        """Deselect all blocks."""
        for block in self.memory_blocks:
            block.selected = False

    def get_selected_block(self) -> Optional[MemoryBlock]:
        """Get the currently selected block."""
        for block in self.memory_blocks:
            if block.selected:
                return block
        return None

    def promote_to_old_generation(self, block_id: int) -> bool:
        """Promote a block from young to old generation."""
        block = self.get_block_by_id(block_id)
        if block and block.generation == Generation.YOUNG:
            block.generation = Generation.OLD
            return True
        return False

    def add_reference(self, from_id: int, to_id: int) -> bool:
        """Add a reference from one block to another."""
        from_block = self.get_block_by_id(from_id)
        to_block = self.get_block_by_id(to_id)

        if from_block and to_block:
            from_block.add_reference(to_id)
            return True
        return False

    def remove_reference(self, from_id: int, to_id: int) -> bool:
        """Remove a reference from one block to another."""
        from_block = self.get_block_by_id(from_id)

        if from_block:
            from_block.remove_reference(to_id)
            return True
        return False

    def get_used_memory(self) -> int:
        """Get the amount of used memory."""
        return sum(block.size for block in self.memory_blocks)

    def get_free_memory(self) -> int:
        """Get the amount of free memory."""
        return self.total_memory_size - self.get_used_memory()

    def _find_free_space_index(self, size: int) -> int:
        """Find the starting index for a new block of the given size."""
        if not self.memory_blocks:
            return 0  # Memory is completely empty

        # Sort blocks by start_index
        sorted_blocks = sorted(self.memory_blocks, key=lambda block: block.start_index)

        # Check for space at the beginning
        if sorted_blocks[0].start_index >= size:
            return 0

        # Check for space between blocks
        for i in range(len(sorted_blocks) - 1):
            current_block = sorted_blocks[i]
            next_block = sorted_blocks[i + 1]
            gap_size = next_block.start_index - (current_block.end_index + 1)

            if gap_size >= size:
                return current_block.end_index + 1

        # Check for space at the end
        last_block = sorted_blocks[-1]
        remaining_space = self.total_memory_size - (last_block.end_index + 1)

        if remaining_space >= size:
            return last_block.end_index + 1

        return -1  # No suitable space found

    def _find_insert_index(self, start_index: int) -> int:
        """Find the index to insert a new block at."""
        for i, block in enumerate(self.memory_blocks):
            if block.start_index > start_index:
                return i
        return len(self.memory_blocks)

    def calculate_fragmentation(self) -> int:
        """Calculate memory fragmentation as a percentage."""
        if len(self.memory_blocks) <= 1:
            return 0  # No fragmentation with 0 or 1 blocks

        # Sort blocks by start_index
        sorted_blocks = sorted(self.memory_blocks, key=lambda block: block.start_index)

        # Calculate total gaps between blocks
        total_gap_size = 0

        # Gap at the beginning
        total_gap_size += sorted_blocks[0].start_index

        # Gaps between blocks
        for i in range(len(sorted_blocks) - 1):
            current_block = sorted_blocks[i]
            next_block = sorted_blocks[i + 1]
            gap_size = next_block.start_index - (current_block.end_index + 1)
            total_gap_size += max(0, gap_size)

        # Gap at the end
        last_block = sorted_blocks[-1]
        total_gap_size += self.total_memory_size - (last_block.end_index + 1)

        # Calculate fragmentation as percentage of free memory that's fragmented
        free_memory = self.get_free_memory()
        return round((total_gap_size / free_memory) * 100) if free_memory else 0
