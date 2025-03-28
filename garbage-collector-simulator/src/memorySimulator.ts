import {
  MemoryBlock,
  MemoryBlockStatus,
  MemoryAllocationResult,
  GCStats
} from './types';

export class MemorySimulator {
  private memoryBlocks: MemoryBlock[] = [];
  private totalMemorySize: number;
  private nextBlockId = 1;

  constructor(totalSize: number) {
    this.totalMemorySize = totalSize;
    // Initialize with all free memory
    this.reset();
  }

  public reset(): void {
    this.memoryBlocks = [];
    this.nextBlockId = 1;
  }

  public allocateMemory(size: number): MemoryAllocationResult {
    if (size <= 0) {
      return {
        success: false,
        error: 'Block size must be greater than 0'
      };
    }

    if (size > this.totalMemorySize) {
      return {
        success: false,
        error: `Block size exceeds total memory (${this.totalMemorySize})`
      };
    }

    // Check if we have enough free space
    const freeMemory = this.getFreeMemory();
    if (size > freeMemory) {
      return {
        success: false,
        error: `Not enough free memory. Requested ${size}, available ${freeMemory}`
      };
    }

    // Find a suitable position for the new block
    const startIndex = this.findFreeSpaceStartIndex(size);
    if (startIndex === -1) {
      return {
        success: false,
        error: 'Memory too fragmented. Try compacting memory or freeing some blocks.'
      };
    }

    // Create a new memory block
    const randomColor = this.getRandomColor();
    const newBlock: MemoryBlock = {
      id: this.nextBlockId++,
      size,
      status: MemoryBlockStatus.ALLOCATED,
      color: randomColor,
      startIndex,
      endIndex: startIndex + size - 1,
      allocationTime: Date.now(),
      selected: false,
      // New blocks are allocated to the young generation by default
      generation: 'young'
    };

    // Insert the block at the correct position to maintain order by startIndex
    const insertIndex = this.findInsertIndex(startIndex);
    this.memoryBlocks.splice(insertIndex, 0, newBlock);

    return {
      success: true,
      block: newBlock
    };
  }

  public markAsGarbage(blockId: number): boolean {
    const block = this.getBlockById(blockId);
    if (block && block.status === MemoryBlockStatus.ALLOCATED) {
      block.status = MemoryBlockStatus.GARBAGE;
      return true;
    }
    return false;
  }

  public freeBlock(blockId: number): boolean {
    const index = this.memoryBlocks.findIndex(block => block.id === blockId);
    if (index !== -1) {
      this.memoryBlocks.splice(index, 1);
      return true;
    }
    return false;
  }

  public markBlock(blockId: number): boolean {
    const block = this.getBlockById(blockId);
    if (block && (block.status === MemoryBlockStatus.ALLOCATED || block.status === MemoryBlockStatus.GARBAGE)) {
      block.status = MemoryBlockStatus.MARKED;
      return true;
    }
    return false;
  }

  public compactMemory(): void {
    // Sort blocks by startIndex
    this.memoryBlocks.sort((a, b) => a.startIndex - b.startIndex);

    // Relocate blocks to eliminate fragmentation
    let currentIndex = 0;
    for (const block of this.memoryBlocks) {
      block.startIndex = currentIndex;
      block.endIndex = currentIndex + block.size - 1;
      currentIndex += block.size;
    }
  }

  public getStats(): GCStats {
    const usedMemory = this.getUsedMemory();
    const freeMemory = this.getFreeMemory();
    const fragmentation = this.calculateFragmentation();

    return {
      totalMemory: this.totalMemorySize,
      usedMemory,
      freeMemory,
      fragmentation,
      lastGCDuration: 0, // Will be set by GC
      memoryReclaimed: 0 // Will be set by GC
    };
  }

  public getAllBlocks(): MemoryBlock[] {
    return [...this.memoryBlocks];
  }

  public getBlockById(id: number): MemoryBlock | undefined {
    return this.memoryBlocks.find(block => block.id === id);
  }

  public selectBlock(id: number): void {
    // Deselect all blocks first
    this.memoryBlocks.forEach(block => block.selected = false);

    // Select the specified block
    const block = this.getBlockById(id);
    if (block) {
      block.selected = true;
    }
  }

  public deselectAllBlocks(): void {
    this.memoryBlocks.forEach(block => block.selected = false);
  }

  public getSelectedBlock(): MemoryBlock | undefined {
    return this.memoryBlocks.find(block => block.selected);
  }

  public promoteToOldGeneration(blockId: number): boolean {
    const block = this.getBlockById(blockId);
    if (block && block.generation === 'young') {
      block.generation = 'old';
      return true;
    }
    return false;
  }

  private getUsedMemory(): number {
    return this.memoryBlocks.reduce((total, block) => total + block.size, 0);
  }

  private getFreeMemory(): number {
    return this.totalMemorySize - this.getUsedMemory();
  }

  private findFreeSpaceStartIndex(size: number): number {
    if (this.memoryBlocks.length === 0) {
      return 0; // Memory is completely empty
    }

    // Sort blocks by startIndex to ensure correct free space calculation
    const sortedBlocks = [...this.memoryBlocks].sort((a, b) => a.startIndex - b.startIndex);

    // Check for space at the beginning
    if (sortedBlocks[0].startIndex >= size) {
      return 0;
    }

    // Check for space between blocks
    for (let i = 0; i < sortedBlocks.length - 1; i++) {
      const currentBlock = sortedBlocks[i];
      const nextBlock = sortedBlocks[i + 1];
      const gapSize = nextBlock.startIndex - (currentBlock.endIndex + 1);

      if (gapSize >= size) {
        return currentBlock.endIndex + 1;
      }
    }

    // Check for space at the end
    const lastBlock = sortedBlocks[sortedBlocks.length - 1];
    const remainingSpace = this.totalMemorySize - (lastBlock.endIndex + 1);

    if (remainingSpace >= size) {
      return lastBlock.endIndex + 1;
    }

    return -1; // No suitable space found
  }

  private findInsertIndex(startIndex: number): number {
    for (let i = 0; i < this.memoryBlocks.length; i++) {
      if (this.memoryBlocks[i].startIndex > startIndex) {
        return i;
      }
    }
    return this.memoryBlocks.length;
  }

  private calculateFragmentation(): number {
    if (this.memoryBlocks.length <= 1) {
      return 0; // No fragmentation with 0 or 1 blocks
    }

    // Sort blocks by startIndex
    const sortedBlocks = [...this.memoryBlocks].sort((a, b) => a.startIndex - b.startIndex);

    // Calculate total gaps between blocks
    let totalGapSize = 0;

    // Gap at the beginning
    totalGapSize += sortedBlocks[0].startIndex;

    // Gaps between blocks
    for (let i = 0; i < sortedBlocks.length - 1; i++) {
      const currentBlock = sortedBlocks[i];
      const nextBlock = sortedBlocks[i + 1];
      const gapSize = nextBlock.startIndex - (currentBlock.endIndex + 1);
      totalGapSize += Math.max(0, gapSize);
    }

    // Gap at the end
    const lastBlock = sortedBlocks[sortedBlocks.length - 1];
    totalGapSize += this.totalMemorySize - (lastBlock.endIndex + 1);

    // Calculate fragmentation as percentage of free memory that's fragmented
    const freeMemory = this.getFreeMemory();
    return freeMemory === 0 ? 0 : Math.round((totalGapSize / freeMemory) * 100);
  }

  private getRandomColor(): string {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#FF9F1C', '#3BCEAC', '#6A0572',
      '#4D80E4', '#FF7A5A', '#5D5C61', '#938BA1', '#7AC74F',
      '#F4D35E', '#EE6055', '#60D394', '#AAF683', '#FFD97D'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  }
}
