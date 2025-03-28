import './styles.css';
import { MemorySimulator } from './memorySimulator';
import { GarbageCollector } from './garbageCollector';
import { UIController } from './uiController';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  // Create instances of our classes
  const memorySimulator = new MemorySimulator(100); // 100 memory blocks
  const garbageCollector = new GarbageCollector(memorySimulator);
  const uiController = new UIController(memorySimulator, garbageCollector);

  // Initialize the UI
  uiController.initialize();
});
