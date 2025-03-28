import { MemorySimulator } from './memorySimulator';
import {
  MemoryBlock,
  MemoryBlockStatus,
  GCAlgorithm,
  GCResult
} from './types';

export class GarbageCollector {
  private memorySimulator: MemorySimulator;
  private algorithm: GCAlgorithm = GCAlgorithm.MARK_SWEEP;
  private threshold = 70; // Default: run GC when memory is 70% full
  private autoGC = false;

  private youngGenMaxAge = 5000; // 5 seconds in ms - for generational GC

  constructor(memorySimulator: MemorySimulator) {
    this.memorySimulator = memorySimulator;
  }

  public setAlgorithm(algorithm: GCAlgorithm): void {
    this.algorithm = algorithm;
  }

  public setThreshold(threshold: number): void {
    this.threshold = Math.max(1, Math.min(100, threshold));
  }

  public setAutoGC(autoGC: boolean): void {
    this.autoGC = autoGC;
  }

  public isAutoGCEnabled(): boolean {
    return this.autoGC;
  }

  public getThreshold(): number {
    return this.threshold;
  }

  public getCurrentAlgorithm(): GCAlgorithm {
    return this.algorithm;
  }

  public checkAndRunAutoGC(): GCResult | null {
    if (!this.autoGC) {
      return null;
    }

    const stats = this.memorySimulator.getStats();
    const memoryUsagePercent = (stats.usedMemory / stats.totalMemory) * 100;

    if (memoryUsagePercent >= this.threshold) {
      return this.runGarbageCollection();
    }

    return null;
  }

  public runGarbageCollection(): GCResult {
    const startTime = performance.now();
    let reclaimedBlocks: MemoryBlock[] = [];

    switch (this.algorithm) {
      case GCAlgorithm.MARK_SWEEP:
        reclaimedBlocks = this.markAndSweep();
        break;
      case GCAlgorithm.GENERATIONAL:
        reclaimedBlocks = this.generationalGC();
        break;
    }

    const endTime = performance.now();
    const duration = endTime - startTime;

    return {
      reclaimedBlocks,
      duration
    };
  }

  private markAndSweep(): MemoryBlock[] {
    const reclaimedBlocks: MemoryBlock[] = [];
    const allBlocks = this.memorySimulator.getAllBlocks();

    // Mark phase: Simply mark all blocks that are not garbage (in a real system, we'd traverse references)
    for (const block of allBlocks) {
      if (block.status === MemoryBlockStatus.ALLOCATED) {
        this.memorySimulator.markBlock(block.id);
      }
    }

    // Sweep phase: Remove all unmarked blocks (garbage)
    for (const block of [...allBlocks]) {
      if (block.status === MemoryBlockStatus.GARBAGE) {
        if (this.memorySimulator.freeBlock(block.id)) {
          reclaimedBlocks.push(block);
        }
      }
    }

    // Reset all marked blocks back to allocated
    for (const block of this.memorySimulator.getAllBlocks()) {
      if (block.status === MemoryBlockStatus.MARKED) {
        block.status = MemoryBlockStatus.ALLOCATED;
      }
    }

    return reclaimedBlocks;
  }

  private generationalGC(): MemoryBlock[] {
    const reclaimedBlocks: MemoryBlock[] = [];
    const allBlocks = this.memorySimulator.getAllBlocks();
    const currentTime = Date.now();

    // First, promote any young objects that have survived long enough
    for (const block of allBlocks) {
      if (
        block.generation === 'young' &&
        block.status === MemoryBlockStatus.ALLOCATED &&
        currentTime - block.allocationTime > this.youngGenMaxAge
      ) {
        this.memorySimulator.promoteToOldGeneration(block.id);
      }
    }

    // Young generation collection (minor GC) - collects all garbage in young generation
    for (const block of [...allBlocks]) {
      if (
        block.generation === 'young' &&
        block.status === MemoryBlockStatus.GARBAGE
      ) {
        if (this.memorySimulator.freeBlock(block.id)) {
          reclaimedBlocks.push(block);
        }
      }
    }

    // Occasionally do a full collection (major GC) - 25% chance each time
    const shouldRunMajorGC = Math.random() < 0.25;

    if (shouldRunMajorGC) {
      for (const block of [...this.memorySimulator.getAllBlocks()]) {
        if (
          block.generation === 'old' &&
          block.status === MemoryBlockStatus.GARBAGE
        ) {
          if (this.memorySimulator.freeBlock(block.id)) {
            reclaimedBlocks.push(block);
          }
        }
      }
    }

    return reclaimedBlocks;
  }
}
