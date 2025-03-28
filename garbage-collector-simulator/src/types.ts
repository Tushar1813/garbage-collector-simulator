export enum MemoryBlockStatus {
  FREE = 'free',
  ALLOCATED = 'allocated',
  MARKED = 'marked',
  GARBAGE = 'garbage'
}

export enum GCAlgorithm {
  MARK_SWEEP = 'mark-sweep',
  GENERATIONAL = 'generational'
}

export interface MemoryBlock {
  id: number;
  size: number;
  status: MemoryBlockStatus;
  color: string;
  startIndex: number;
  endIndex: number;
  generation?: 'young' | 'old';
  allocationTime: number;
  selected: boolean;
}

export interface GCStats {
  totalMemory: number;
  usedMemory: number;
  freeMemory: number;
  fragmentation: number;
  lastGCDuration: number;
  memoryReclaimed: number;
}

export interface MemoryAllocationResult {
  success: boolean;
  block?: MemoryBlock;
  error?: string;
}

export interface GCResult {
  reclaimedBlocks: MemoryBlock[];
  duration: number;
}
