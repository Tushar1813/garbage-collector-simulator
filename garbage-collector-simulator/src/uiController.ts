import { MemorySimulator } from './memorySimulator';
import { GarbageCollector } from './garbageCollector';
import {
  MemoryBlockStatus,
  GCAlgorithm,
  GCResult,
  GCStats
} from './types';

export class UIController {
  private memorySimulator: MemorySimulator;
  private garbageCollector: GarbageCollector;
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private blockHeight = 40;
  private animating = false;

  // Refresh rate for UI updates (ms)
  private refreshRate = 100;

  constructor(memorySimulator: MemorySimulator, garbageCollector: GarbageCollector) {
    this.memorySimulator = memorySimulator;
    this.garbageCollector = garbageCollector;

    // Get canvas and context
    this.canvas = document.getElementById('memory-canvas') as HTMLCanvasElement;
    this.ctx = this.canvas.getContext('2d') as CanvasRenderingContext2D;
  }

  public initialize(): void {
    // Set up event listeners
    this.setupEventListeners();

    // Initial render
    this.updateUI();

    // Start the refresh interval
    window.setInterval(() => {
      // Check if auto GC should run
      const gcResult = this.garbageCollector.checkAndRunAutoGC();
      if (gcResult && gcResult.reclaimedBlocks.length > 0) {
        this.updateGCStats(gcResult);
      }

      this.updateUI();
    }, this.refreshRate);

    // Update the explanation panel based on the current algorithm
    this.updateAlgorithmExplanation(GCAlgorithm.MARK_SWEEP);
  }

  private setupEventListeners(): void {
    // Algorithm selection
    const algorithmSelect = document.getElementById('gc-algorithm') as HTMLSelectElement;
    algorithmSelect.addEventListener('change', () => {
      const algorithm = algorithmSelect.value as GCAlgorithm;
      this.garbageCollector.setAlgorithm(algorithm);
      this.updateAlgorithmExplanation(algorithm);
    });

    // Allocate memory button
    const allocateBtn = document.getElementById('allocate') as HTMLButtonElement;
    allocateBtn.addEventListener('click', () => {
      // Random size between 1 and 10
      const size = Math.floor(Math.random() * 10) + 1;
      const result = this.memorySimulator.allocateMemory(size);

      if (!result.success && result.error) {
        alert(result.error);
      }

      this.updateUI();
    });

    // Dereference button
    const dereferenceBtn = document.getElementById('dereference') as HTMLButtonElement;
    dereferenceBtn.addEventListener('click', () => {
      const selectedBlock = this.memorySimulator.getSelectedBlock();
      if (selectedBlock && selectedBlock.status === MemoryBlockStatus.ALLOCATED) {
        this.memorySimulator.markAsGarbage(selectedBlock.id);
        this.updateUI();
      } else {
        alert('Please select an allocated block to dereference');
      }
    });

    // Run GC button
    const runGCBtn = document.getElementById('run-gc') as HTMLButtonElement;
    runGCBtn.addEventListener('click', () => {
      this.runGarbageCollectionWithAnimation();
    });

    // Compact memory button
    const compactBtn = document.getElementById('compact') as HTMLButtonElement;
    compactBtn.addEventListener('click', () => {
      this.memorySimulator.compactMemory();
      this.updateUI();
    });

    // Reset button
    const resetBtn = document.getElementById('reset') as HTMLButtonElement;
    resetBtn.addEventListener('click', () => {
      this.memorySimulator.reset();
      this.updateUI();
    });

    // Auto GC checkbox
    const autoGCCheckbox = document.getElementById('auto-gc') as HTMLInputElement;
    autoGCCheckbox.addEventListener('change', () => {
      this.garbageCollector.setAutoGC(autoGCCheckbox.checked);
    });

    // Threshold slider
    const thresholdSlider = document.getElementById('threshold') as HTMLInputElement;
    const thresholdValue = document.getElementById('threshold-value') as HTMLSpanElement;

    thresholdSlider.addEventListener('input', () => {
      const value = parseInt(thresholdSlider.value);
      thresholdValue.textContent = `${value}%`;
      this.garbageCollector.setThreshold(value);
    });

    // Canvas click handler for block selection
    this.canvas.addEventListener('click', (event) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      this.handleCanvasClick(x, y);
    });
  }

  private updateUI(): void {
    this.renderMemory();
    this.updateStats();
  }

  private renderMemory(): void {
    // Clear the canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Calculate block dimensions
    const canvasWidth = this.canvas.width;
    const canvasHeight = this.canvas.height;
    const blockWidth = canvasWidth / 100; // Each block is 1/100 of the width

    // Draw memory grid background
    this.ctx.fillStyle = '#f0f0f0';
    this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw grid lines
    this.ctx.strokeStyle = '#ddd';
    this.ctx.lineWidth = 0.5;

    for (let i = 0; i <= 100; i += 10) {
      const x = i * blockWidth;

      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, canvasHeight);
      this.ctx.stroke();

      // Add scale numbers every 10 blocks
      this.ctx.fillStyle = '#666';
      this.ctx.font = '10px Arial';
      this.ctx.fillText(i.toString(), x + 2, 10);
    }

    // Draw blocks
    const blocks = this.memorySimulator.getAllBlocks();
    const algorithm = this.garbageCollector.getCurrentAlgorithm();

    for (const block of blocks) {
      const x = block.startIndex * blockWidth;
      const width = block.size * blockWidth;
      const y = canvasHeight / 2 - this.blockHeight / 2;

      // Adjust y position for generational GC
      let adjustedY = y;
      if (algorithm === GCAlgorithm.GENERATIONAL && block.generation) {
        adjustedY = block.generation === 'young'
          ? y - this.blockHeight * 0.6
          : y + this.blockHeight * 0.6;
      }

      // Set color based on status
      let fillColor = block.color;
      const borderColor = 'black';

      if (block.status === MemoryBlockStatus.GARBAGE) {
        fillColor = '#ccc'; // Gray for garbage
      } else if (block.status === MemoryBlockStatus.MARKED) {
        fillColor = '#90EE90'; // Light green for marked
      }

      // Draw the block
      this.ctx.fillStyle = fillColor;
      this.ctx.strokeStyle = borderColor;
      this.ctx.lineWidth = block.selected ? 3 : 1;

      this.ctx.beginPath();
      this.ctx.rect(x, adjustedY, width, this.blockHeight);
      this.ctx.fill();
      this.ctx.stroke();

      // Draw block ID
      this.ctx.fillStyle = 'black';
      this.ctx.font = '12px Arial';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(block.id.toString(), x + width / 2, adjustedY + this.blockHeight / 2 + 4);

      // Draw block size below
      this.ctx.font = '10px Arial';
      this.ctx.fillText(`${block.size}`, x + width / 2, adjustedY + this.blockHeight + 10);

      // For generational GC, add generation label
      if (algorithm === GCAlgorithm.GENERATIONAL && block.generation) {
        this.ctx.font = '10px Arial';
        this.ctx.fillText(
          block.generation.substring(0, 1).toUpperCase(),
          x + width / 2,
          adjustedY - 5
        );
      }
    }

    // Draw algorithm-specific visualizations
    if (algorithm === GCAlgorithm.GENERATIONAL) {
      // Draw generation regions
      this.ctx.font = '14px Arial';
      this.ctx.fillStyle = '#333';
      this.ctx.textAlign = 'left';

      this.ctx.fillText('Young Generation', 10, canvasHeight / 2 - this.blockHeight);
      this.ctx.fillText('Old Generation', 10, canvasHeight / 2 + this.blockHeight * 1.5);

      // Draw dividing line
      this.ctx.strokeStyle = '#999';
      this.ctx.lineWidth = 1;
      this.ctx.setLineDash([5, 3]);

      this.ctx.beginPath();
      this.ctx.moveTo(0, canvasHeight / 2);
      this.ctx.lineTo(canvasWidth, canvasHeight / 2);
      this.ctx.stroke();

      this.ctx.setLineDash([]);
    }
  }

  private updateStats(): void {
    const stats = this.memorySimulator.getStats();

    // Update stats in the UI
    document.getElementById('total-memory')!.textContent = `${stats.totalMemory} blocks`;
    document.getElementById('used-memory')!.textContent = `${stats.usedMemory} blocks`;
    document.getElementById('free-memory')!.textContent = `${stats.freeMemory} blocks`;
    document.getElementById('fragmentation')!.textContent = `${stats.fragmentation}%`;
    document.getElementById('gc-duration')!.textContent = `${stats.lastGCDuration.toFixed(2)} ms`;
    document.getElementById('memory-reclaimed')!.textContent = `${stats.memoryReclaimed} blocks`;
  }

  private updateGCStats(result: GCResult): void {
    const stats = this.memorySimulator.getStats() as GCStats;

    // Update GC specific stats
    stats.lastGCDuration = result.duration;
    stats.memoryReclaimed = result.reclaimedBlocks.reduce((total, block) => total + block.size, 0);

    // Update stats in the UI
    document.getElementById('gc-duration')!.textContent = `${stats.lastGCDuration.toFixed(2)} ms`;
    document.getElementById('memory-reclaimed')!.textContent = `${stats.memoryReclaimed} blocks`;
  }

  private handleCanvasClick(x: number, y: number): void {
    const blocks = this.memorySimulator.getAllBlocks();
    const canvasWidth = this.canvas.width;
    const blockWidth = canvasWidth / 100;
    const canvasHeight = this.canvas.height;

    // Check which block was clicked
    for (const block of blocks) {
      const blockX = block.startIndex * blockWidth;
      const blockWidth_ = block.size * blockWidth;
      const blockY = canvasHeight / 2 - this.blockHeight / 2;

      // Adjust y position for generational GC
      let adjustedY = blockY;
      if (this.garbageCollector.getCurrentAlgorithm() === GCAlgorithm.GENERATIONAL && block.generation) {
        adjustedY = block.generation === 'young'
          ? blockY - this.blockHeight * 0.6
          : blockY + this.blockHeight * 0.6;
      }

      // Check if click is within the block
      if (
        x >= blockX &&
        x <= blockX + blockWidth_ &&
        y >= adjustedY &&
        y <= adjustedY + this.blockHeight
      ) {
        this.memorySimulator.selectBlock(block.id);
        this.updateUI();
        return;
      }
    }

    // If we get here, no block was clicked
    this.memorySimulator.deselectAllBlocks();
    this.updateUI();
  }

  private async runGarbageCollectionWithAnimation(): Promise<void> {
    if (this.animating) {
      return; // Don't run if already animating
    }

    this.animating = true;

    const blocks = this.memorySimulator.getAllBlocks();
    const algorithm = this.garbageCollector.getCurrentAlgorithm();

    // Animate mark phase
    if (algorithm === GCAlgorithm.MARK_SWEEP) {
      // Mark all allocated blocks
      for (const block of blocks) {
        if (block.status === MemoryBlockStatus.ALLOCATED) {
          // Animate marking
          block.status = MemoryBlockStatus.MARKED;
          this.updateUI();
          await this.sleep(50); // Short delay between each mark
        }
      }

      await this.sleep(500); // Pause between mark and sweep
    }

    // Run actual garbage collection
    const gcResult = this.garbageCollector.runGarbageCollection();

    // Update stats
    this.updateGCStats(gcResult);

    // Final UI update
    this.updateUI();
    this.animating = false;
  }

  private updateAlgorithmExplanation(algorithm: GCAlgorithm): void {
    const algorithmInfo = document.getElementById('algorithm-info') as HTMLDivElement;

    if (algorithm === GCAlgorithm.MARK_SWEEP) {
      algorithmInfo.innerHTML = `
        <h3>Mark and Sweep Algorithm</h3>
        <p>The Mark and Sweep algorithm works in two phases:</p>
        <ol>
          <li><strong>Mark Phase:</strong> The garbage collector identifies all objects that are still in use (referenced) and marks them.</li>
          <li><strong>Sweep Phase:</strong> The garbage collector scans the entire memory and reclaims any objects that are not marked.</li>
        </ol>
        <p>This is a simple but effective algorithm used in many programming languages.</p>
      `;
    } else if (algorithm === GCAlgorithm.GENERATIONAL) {
      algorithmInfo.innerHTML = `
        <h3>Generational Garbage Collection</h3>
        <p>Generational GC divides memory into regions based on object age:</p>
        <ul>
          <li><strong>Young Generation:</strong> New objects are allocated here. Most objects die young, so this region is collected frequently.</li>
          <li><strong>Old Generation:</strong> Objects that survive multiple young gen collections are promoted here. This region is collected less frequently.</li>
        </ul>
        <p>This approach is more efficient because it focuses collection efforts where they'll have the most impact.</p>
        <p>Used in high-performance VMs like JVM, .NET CLR, and modern JavaScript engines.</p>
      `;
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
