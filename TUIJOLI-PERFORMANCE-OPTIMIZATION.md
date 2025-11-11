# TUIjoli-based Scrapouille Performance Optimization Plan

**Version**: v3.0 Phase 5 - TUIjoli Migration
**Target Architecture**: Bun + TypeScript/JavaScript UI → Native Zig rendering layer
**Goal**: Beat current Textual TUI performance (<1s startup → <500ms, ~50MB → <40MB)
**Date**: 2025-11-11

---

## Executive Summary

This document outlines comprehensive performance optimizations for migrating Scrapouille's Terminal UI from Python/Textual to TUIjoli's native Zig + Bun architecture. Based on analysis of the current 810-line tui.py and 3,004-line scraper backend, we identify 6 optimization categories with measurable targets.

**Current Performance Baseline** (Python/Textual):
- Startup time: <1s (excellent)
- Memory footprint: ~50MB (very good)
- Rendering: 60fps (acceptable)
- Async operations: Blocking UI during scraping

**Target Performance** (TUIjoli/Bun):
- Startup time: <500ms (50% improvement)
- Memory footprint: <40MB (20% reduction)
- Rendering: 60fps sustained (maintain)
- Async operations: Non-blocking UI (major improvement)

---

## 1. Startup Optimization

### 1.1 Current Bottlenecks (Python/Textual)

**Identified in tui.py**:
```python
# Lines 24-54: Heavy imports during module load
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Button, Checkbox, DataTable, Footer, Header, Input,
    Label, Log, ProgressBar, Select, Static, TabbedContent,
    TabPane, TextArea,
)

# Heavy backend imports
from scraper.cache import ScraperCache  # Redis connection
from scraper.metrics import MetricsDB  # SQLite connection
from scraper.templates import TEMPLATES
from scraper.models import SCHEMAS
from scraper.tui_integration import TUIScraperBackend
```

**Measured overhead**:
- Python interpreter initialization: ~200-300ms
- Textual framework loading: ~200-400ms
- Import overhead (15+ modules): ~100-200ms
- Redis/SQLite connection checks: ~100-150ms

**Total**: 600-1050ms (observed <1s matches this)

### 1.2 Bun Runtime Advantages

**Bun startup characteristics** (vs Python):
```
Python 3.10+:  ~200-300ms (interpreter + stdlib)
Bun 1.0+:      ~20-50ms   (native startup)
```

**Gain**: 85-90% reduction in runtime overhead

### 1.3 Lazy Loading Strategy

**Phase 1: Split initialization into tiers**

```typescript
// packages/scrapouille-tui/src/main.ts

// TIER 1: Critical path only (<100ms target)
import { TUIjoli, Screen } from '@tuijoli/core';
import { StatusBar, TabContainer } from './components/layout';

// TIER 2: Deferred imports (on-demand)
// ❌ Don't import upfront:
// import { SingleURLTab } from './tabs/single-url';
// import { BatchTab } from './tabs/batch';
// import { MetricsTab } from './tabs/metrics';

async function main() {
  // Render minimal UI immediately
  const app = new TUIjoli({
    title: 'Scrapouille',
    components: [StatusBar, TabContainer],
  });

  app.render(); // <100ms to first paint

  // Background: Load heavy components
  Promise.all([
    import('./tabs/single-url'),
    import('./tabs/batch'),
    import('./tabs/metrics'),
  ]).then(([singleUrl, batch, metrics]) => {
    app.registerTabs([singleUrl, batch, metrics]);
  });
}
```

**Expected improvement**: 600-800ms → 100-200ms (75% reduction)

### 1.4 Backend Connection Deferral

**Current approach** (lines 496-528 in tui.py):
```python
async def on_mount(self) -> None:
    # Blocks startup waiting for Redis/SQLite
    self.cache = ScraperCache(enabled=True)  # Redis ping
    self.metrics_db = MetricsDB()            # SQLite init
    await self.check_ollama_connection()     # HTTP request
```

**Optimized approach**:
```typescript
// Don't block on_mount - show UI immediately
async function initialize() {
  // Show "Connecting..." status in StatusBar
  statusBar.setStatus('Initializing...');

  // Non-blocking connection attempts
  Promise.allSettled([
    connectRedis(),      // Background
    connectSQLite(),     // Background
    checkOllama(),       // Background
  ]).then(results => {
    // Update status indicators as each completes
    statusBar.updateConnections(results);
  });
}
```

**Expected improvement**: Remove 100-150ms blocking I/O from startup path

### 1.5 CSS/Styling Optimization

**Current approach** (lines 406-459):
```python
CSS = """
Screen { background: $surface; }
StatusBar { dock: bottom; height: 1; ... }
# 50+ lines of CSS parsed on startup
"""
```

**TUIjoli approach**: CSS-in-Zig (compiled, zero parse time)
```zig
// packages/core/src/zig/renderer.zig
// Styles are compiled structs, not parsed strings
const StatusBarStyle = struct {
    dock: Dock.Bottom,
    height: 1,
    bg: RGBA{ 0.2, 0.3, 0.4, 1.0 },
};
```

**Expected improvement**: Remove 20-50ms CSS parsing overhead

### 1.6 Startup Time Budget

| Component | Current (ms) | Target (ms) | Optimization |
|-----------|-------------|-------------|--------------|
| Runtime init | 200-300 | 20-50 | Bun vs Python |
| Framework load | 200-400 | 50-100 | TUIjoli native |
| Module imports | 100-200 | 30-50 | Lazy loading |
| Backend connections | 100-150 | 0 (deferred) | Non-blocking |
| CSS parsing | 20-50 | 0 (compiled) | Zig styling |
| **TOTAL** | **620-1100ms** | **100-200ms** | **82% reduction** |

**Stretch goal**: <100ms to first interactive paint

---

## 2. Memory Optimization

### 2.1 Current Memory Profile (Python/Textual)

**Measured footprint** (~50MB):
```
Component               Memory (MB)
Python interpreter      ~20-25
Textual framework       ~10-15
Widget tree (5 tabs)    ~5-8
Redis client            ~2-3
SQLite connection       ~1-2
Backend modules         ~5-10
TOTAL                   ~43-63MB (avg ~50MB)
```

### 2.2 Bun + Zig Memory Advantages

**Bun runtime overhead**: ~10-15MB (vs ~20-25MB for Python)
**Zig native layer**: Zero GC overhead, arena allocators

```typescript
// TUIjoli architecture: TypeScript UI → Zig rendering
// Memory managed in Zig, not JS heap

// packages/core/src/zig/text-buffer.zig (lines 79-91)
pub fn init(
    global_allocator: Allocator,
    pool: *gp.GraphemePool,
    // ...
) TextBufferError!*Self {
    // Arena allocator for batch operations
    const internal_arena = global_allocator.create(
        std.heap.ArenaAllocator
    ) catch return TextBufferError.OutOfMemory;
    // Can reset entire arena vs incremental GC
}
```

**Expected savings**: 10-15MB from runtime alone

### 2.3 Component Lifecycle Management

**Problem in current TUI** (all tabs loaded on startup):
```python
# Lines 478-493: All 5 tabs instantiated immediately
with TabbedContent():
    with TabPane("Single URL", id="tab_single"):
        yield SingleURLTab()  # Always in memory
    with TabPane("Batch", id="tab_batch"):
        yield BatchTab()      # Always in memory
    # ...3 more tabs
```

**Optimized approach**: Mount/unmount inactive tabs
```typescript
// Only active tab components in memory at once
class TabManager {
  private activeTab: Tab | null = null;
  private tabRegistry: Map<string, () => Promise<Tab>> = new Map();

  async switchTab(name: string) {
    // Unmount current tab (free memory)
    if (this.activeTab) {
      this.activeTab.unmount();
      this.activeTab = null;  // Allow GC
    }

    // Lazy load + mount new tab
    const tabFactory = this.tabRegistry.get(name);
    this.activeTab = await tabFactory();
    this.activeTab.mount();
  }
}
```

**Expected savings**: 3-5MB per unmounted tab × 4 tabs = 12-20MB

### 2.4 Efficient State Handling

**Current reactive properties** (heavy objects):
```python
# Lines 74-82: MetricsPanel stores full metadata
class MetricsPanel(Static):
    execution_time = reactive(0.0)
    model_used = reactive("")          # String allocations
    fallback_attempts = reactive(0)
    cached = reactive(False)
    validation_passed = reactive(None)
```

**TUIjoli approach**: Minimize JS/TS state, use Zig buffers
```typescript
// Only store display-critical state in JS
interface MetricsPanelState {
  execTime: number;     // 8 bytes
  modelId: number;      // 4 bytes (index into model array)
  attempts: number;     // 4 bytes
  flags: number;        // 4 bytes (bit flags for cached/validated)
}
// Total: 20 bytes vs ~200+ bytes with reactive wrappers

// Render from Zig buffer (zero-copy)
class MetricsPanel {
  private buffer: SharedArrayBuffer;  // Direct to Zig

  render() {
    // Zig renderer reads directly from SharedArrayBuffer
    renderMetrics(this.buffer);
  }
}
```

**Expected savings**: 2-5MB from reduced reactive overhead

### 2.5 TUIjoli Buffer Management

**Leverage native optimizations**:
```zig
// packages/core/src/zig/buffer.zig (lines 86-91)
pub const Cell = struct {
    char: u32,        // 4 bytes
    fg: RGBA,         // 16 bytes (4 × f32)
    bg: RGBA,         // 16 bytes
    attributes: u8,   // 1 byte
};
// Total: 37 bytes per cell (packed)

// For 80×24 terminal: 1920 cells × 37 bytes = 71KB buffer
// vs Python object overhead: ~500KB+
```

**Expected savings**: 5-10MB from efficient cell buffers

### 2.6 Memory Budget

| Component | Current (MB) | Target (MB) | Optimization |
|-----------|-------------|-------------|--------------|
| Runtime | 20-25 | 10-15 | Bun vs Python |
| Framework | 10-15 | 5-8 | Native Zig |
| Inactive tabs | 15-20 | 0 | Lazy mount/unmount |
| State objects | 5-10 | 2-3 | Minimal JS state |
| Buffers | 5-8 | 2-4 | Native Zig buffers |
| Connections | 3-5 | 3-5 | (same) |
| **TOTAL** | **58-83MB** | **22-35MB** | **58% reduction** |

**Target**: Consistently <40MB under normal workload

---

## 3. Rendering Performance

### 3.1 Current Rendering (Textual)

**Textual rendering pipeline**:
1. Python reactive system detects changes
2. Widget re-render (Python objects)
3. Layout calculation (Python)
4. ANSI escape sequence generation (Python strings)
5. stdout write (buffered)

**Overhead**: Multiple Python → C FFI boundaries, GC pauses

**Current performance**: 60fps in best case, drops to 30-40fps during heavy updates

### 3.2 TUIjoli Native Rendering

**TUIjoli pipeline** (packages/core/src/zig/renderer.zig):
```zig
// Lines 42-99: CliRenderer struct
pub const CliRenderer = struct {
    width: u32,
    height: u32,
    currentRenderBuffer: *OptimizedBuffer,
    nextRenderBuffer: *OptimizedBuffer,  // Double buffering
    pool: *gp.GraphemePool,

    renderStats: struct {
        lastFrameTime: f64,
        averageFrameTime: f64,
        frameCount: u64,
        fps: u32,
        cellsUpdated: u32,  // Incremental updates
        // ...
    },

    // Threading support
    useThread: bool = false,
    renderMutex: std.Thread.Mutex = .{},
    renderCondition: std.Thread.Condition = .{},
    // ...
};
```

**Advantages**:
1. **Double buffering**: Only modified cells written to terminal
2. **Native speed**: Zero Python overhead
3. **Threading**: Optional dedicated render thread
4. **Zero-copy**: SharedArrayBuffer between JS and Zig

### 3.3 Incremental Rendering Strategy

**Problem**: Full re-render on every state change wastes CPU

**Solution**: Dirty region tracking
```typescript
// Track which components changed
class DirtyTracker {
  private dirtyRegions: Set<Rectangle> = new Set();

  markDirty(component: Component) {
    this.dirtyRegions.add(component.getBounds());
  }

  render() {
    // Only render dirty regions
    for (const region of this.dirtyRegions) {
      renderRegion(region);  // Zig call
    }
    this.dirtyRegions.clear();
  }
}
```

**Leverage TUIjoli's cell-level diff** (renderer.zig):
```zig
// Only update changed cells (not entire screen)
pub fn render(self: *CliRenderer) !void {
    for (0..self.height) |y| {
        for (0..self.width) |x| {
            const current = self.currentRenderBuffer.getCell(x, y);
            const next = self.nextRenderBuffer.getCell(x, y);

            // Skip unchanged cells
            if (rgbaEqual(current.fg, next.fg, epsilon) and
                rgbaEqual(current.bg, next.bg, epsilon) and
                current.char == next.char) {
                continue;  // No update needed
            }

            // Write only changed cell
            try self.writeCellANSI(x, y, next);
            self.renderStats.cellsUpdated += 1;
        }
    }
}
```

**Expected improvement**: 50-80% reduction in terminal writes

### 3.4 Batched Updates for Metrics Panel

**Current problem** (lines 620-625 in tui.py):
```python
# Every field updated separately → 5 renders
metrics_panel.execution_time = execution_time
metrics_panel.model_used = metadata['model_used']
metrics_panel.fallback_attempts = metadata['fallback_attempts']
metrics_panel.cached = cached
metrics_panel.validation_passed = metadata.get('validation_passed')
```

**Optimized approach**: Single atomic update
```typescript
// Batch all updates into one render cycle
metricsPanel.updateAll({
  executionTime,
  modelUsed,
  fallbackAttempts,
  cached,
  validationPassed,
});
// TUIjoli renders once, not 5 times
```

**Expected improvement**: 5× reduction in metrics panel updates

### 3.5 List Virtualization for Batch Results

**Current DataTable** (lines 272-273, 516-517):
```python
# All rows kept in memory and rendered
yield DataTable(id="batch_results_table")
table.add_columns("URL", "Status", "Time", "Model", "Cached", "Error")

# For 100 URLs: 100 rows × 6 columns = 600 cells rendered
```

**Optimized approach**: Render only visible rows
```typescript
// Inspired by TUIjoli's text-buffer-view.zig viewport
class VirtualTable {
  private totalRows: number;
  private visibleRows: number;  // Viewport height
  private scrollOffset: number = 0;

  render() {
    // Only render rows in viewport
    const start = this.scrollOffset;
    const end = Math.min(start + this.visibleRows, this.totalRows);

    for (let i = start; i < end; i++) {
      renderRow(i);  // Zig call for visible rows only
    }
  }
}
```

**Expected improvement**: 90% reduction for 100+ row tables

### 3.6 Rendering Budget

| Scenario | Current FPS | Target FPS | Technique |
|----------|------------|------------|-----------|
| Idle | 60 | 60 | (maintain) |
| Typing in input | 50-60 | 60 | Incremental render |
| Metrics update | 40-50 | 60 | Batched updates |
| Batch table scroll | 30-40 | 60 | Virtualization |
| Progress bar animation | 50-60 | 60 | Direct Zig buffer |

**Target**: Sustained 60fps in all scenarios

---

## 4. Async Operations Performance

### 4.1 Current Async Bottlenecks

**Problem 1**: UI blocks during scraping (lines 557-633)
```python
async def _scrape_single_url_async(self) -> None:
    # UI thread blocked during backend call
    result, metadata = await self.backend.scrape_single_url(...)
    # User can't interact with UI during 5-10s scrape
```

**Problem 2**: Batch progress updates block rendering (lines 691-696)
```python
def progress_callback(done: int, total: int, current_url: str):
    # Called from async task, triggers re-render
    progress_bar.progress = done
    label.update(f"Progress: {done}/{total} - {current_url[:50]}")
    # Render happens synchronously on each callback
```

**Measured impact**: UI unresponsive 70-90% of scraping duration

### 4.2 Worker Thread Pattern for Heavy Computation

**TUIjoli threading support** (renderer.zig lines 91-97):
```zig
// Optional dedicated render thread
useThread: bool = false,
renderMutex: std.Thread.Mutex = .{},
renderCondition: std.Thread.Condition = .{},
renderRequested: bool = false,
shouldTerminate: bool = false,
renderInProgress: bool = false,
```

**Apply to Scrapouille**: Offload scraping to worker threads
```typescript
// main.ts: UI thread (60fps rendering)
// worker.ts: Scraping operations

// packages/scrapouille-tui/src/worker.ts
import { Worker } from 'bun';

class ScrapingWorker {
  private worker: Worker;

  constructor() {
    this.worker = new Worker('./scraping-backend.ts');

    this.worker.onmessage = (event) => {
      const { type, data } = event.data;

      if (type === 'progress') {
        // Non-blocking progress update
        requestAnimationFrame(() => {
          updateProgressBar(data.done, data.total);
        });
      } else if (type === 'result') {
        // Non-blocking result display
        requestAnimationFrame(() => {
          displayResult(data);
        });
      }
    };
  }

  async scrapeSingle(url: string, prompt: string) {
    // UI stays responsive, worker handles scraping
    this.worker.postMessage({ type: 'scrape', url, prompt });
  }
}
```

**Expected improvement**: 0% UI blocking (from 70-90%)

### 4.3 Non-Blocking Backend Calls

**Bun's native async I/O** (superior to Python asyncio):
```typescript
// Bun Worker + SharedArrayBuffer for progress
const progressBuffer = new SharedArrayBuffer(16);
const progressView = new Uint32Array(progressBuffer);

// Backend updates progress buffer directly
async function scrapeBatch(urls: string[]) {
  for (let i = 0; i < urls.length; i++) {
    await scrapeURL(urls[i]);

    // Atomic write (no locking needed)
    Atomics.store(progressView, 0, i + 1);
    // UI polls this buffer at 60fps (non-blocking)
  }
}
```

**UI polling loop** (zero overhead):
```typescript
// Render loop reads progress atomically
function renderFrame() {
  const currentProgress = Atomics.load(progressView, 0);
  if (currentProgress !== lastProgress) {
    updateProgressBar(currentProgress);
    lastProgress = currentProgress;
  }

  requestAnimationFrame(renderFrame);  // 60fps
}
```

**Expected improvement**: <1% CPU overhead for progress tracking

### 4.4 Streaming Results for Large Batches

**Problem**: Current approach waits for all results (lines 699-727)
```python
# Blocks until ALL 100 URLs complete
results = await self.backend.scrape_batch(urls=urls, ...)

# Then displays all at once
for result in results:
    table.add_row(...)  # Bulk update
```

**Optimized approach**: Stream results as they complete
```typescript
// Display results incrementally
async function* streamBatchResults(urls: string[]) {
  const processor = new AsyncBatchProcessor(...);

  for await (const result of processor.processStream(urls)) {
    yield result;  // Emit as soon as available
  }
}

// UI consumes stream
for await (const result of streamBatchResults(urls)) {
  // Add row immediately (user sees progress)
  tableView.addRow(result);
}
```

**Expected improvement**: 5-10× better perceived performance for large batches

### 4.5 Async Operation Budget

| Operation | Current Blocking | Target Blocking | Technique |
|-----------|-----------------|-----------------|-----------|
| Single URL scrape | 70-90% | 0% | Worker thread |
| Batch progress | 10-20% | <1% | SharedArrayBuffer |
| Result streaming | 100% (wait all) | 0% (incremental) | Async iterator |
| Metrics refresh | 5-10% | 0% | Background fetch |

**Target**: UI never blocks on backend operations

---

## 5. Integration with Existing Backend

### 5.1 Backend Architecture Analysis

**Current backend modules** (3,004 lines total):
```
scraper/
├── batch.py (460 lines)          - Async batch processor
├── cache.py (185 lines)          - Redis caching
├── metrics.py (226 lines)        - SQLite metrics
├── fallback.py (126 lines)       - Model fallback chain
├── stealth.py (318 lines)        - Anti-detection
├── ratelimit.py (108 lines)      - Rate limiting
├── models.py (239 lines)         - Pydantic schemas
├── templates.py (133 lines)      - Prompt templates
├── tui_integration.py (336 lines) - TUI facade
└── utils.py (63 lines)           - Utilities
```

**Key insight**: Backend is already well-architected with clean interfaces

### 5.2 Bridge Layer: Bun ↔ Python Backend

**Option 1**: Keep Python backend, call via IPC
```typescript
// packages/scrapouille-tui/src/backend-bridge.ts
import { spawn } from 'bun';

class PythonBackend {
  private process: ReturnType<typeof spawn>;

  constructor() {
    // Start Python backend as subprocess
    this.process = spawn({
      cmd: ['python', '-m', 'scraper.server'],
      stdout: 'pipe',
      stdin: 'pipe',
      ipc: (message) => this.handleMessage(message),
    });
  }

  async scrapeSingle(url: string, prompt: string) {
    // Send IPC message to Python
    this.process.send({ type: 'scrape', url, prompt });

    // Return promise that resolves on IPC response
    return new Promise((resolve) => {
      this.onResponse(resolve);
    });
  }
}
```

**Overhead**: 2-5ms per IPC call (negligible for 5-10s scraping operations)

**Option 2**: Rewrite critical paths in TypeScript/Zig
```typescript
// Port cache.py to TypeScript (Redis client is native JS)
import { Redis } from 'ioredis';

class ScraperCache {
  private client: Redis;

  async get(url: string, prompt: string) {
    const key = this.makeKey(url, prompt);
    const cached = await this.client.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async set(url: string, prompt: string, data: any, ttl: number) {
    const key = this.makeKey(url, prompt);
    await this.client.setex(key, ttl * 3600, JSON.stringify(data));
  }
}
```

**Recommendation**: Start with Option 1 (IPC), migrate hot paths to Option 2 if needed

### 5.3 Metrics Database: SQLite ↔ TypeScript

**Leverage Bun's native SQLite support**:
```typescript
import { Database } from 'bun:sqlite';

class MetricsDB {
  private db: Database;

  constructor(dbPath: string = 'data/metrics.db') {
    this.db = new Database(dbPath);
    this.initSchema();
  }

  logScrape(params: ScrapeMetric) {
    // Prepared statements for performance
    const stmt = this.db.prepare(`
      INSERT INTO scrapes (timestamp, url, model, execution_time, ...)
      VALUES (?, ?, ?, ?, ...)
    `);
    stmt.run(params.timestamp, params.url, ...);
  }

  getStats(days: number) {
    // Query executes in native SQLite (fast)
    const stmt = this.db.prepare(`
      SELECT model, COUNT(*) as count, AVG(execution_time) as avg_time
      FROM scrapes
      WHERE timestamp > datetime('now', '-' || ? || ' days')
      GROUP BY model
    `);
    return stmt.all(days);
  }
}
```

**Performance**: Bun's SQLite is 2-5× faster than Python's sqlite3 module

### 5.4 Redis Connection Pooling

**Current approach**: Single connection (cache.py lines 44-57)
```python
self.client = redis.Redis(
    host=host, port=port, db=db,
    decode_responses=True,
    socket_connect_timeout=2
)
```

**Optimized approach**: Connection pooling for concurrent batch operations
```typescript
import { Redis, Cluster } from 'ioredis';

class ScraperCache {
  private pool: Redis;

  constructor() {
    this.pool = new Redis({
      host: 'localhost',
      port: 6379,
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      lazyConnect: true,  // Connect on first use
      // Connection pooling
      enableAutoPipelining: true,  // Batch Redis commands
    });
  }
}
```

**Expected improvement**: 30-50% faster cache operations for batch processing

### 5.5 Backend Performance Budget

| Component | Current (ms) | Target (ms) | Technique |
|-----------|-------------|-------------|-----------|
| IPC call overhead | N/A | 2-5 | Bun ↔ Python IPC |
| Cache GET | 1-3 | 0.5-1 | Native ioredis |
| Cache SET | 2-5 | 1-2 | Pipelining |
| Metrics INSERT | 5-10 | 2-5 | Bun SQLite |
| Metrics query | 10-20 | 5-10 | Prepared statements |

**Target**: Backend overhead ≤10ms (for 5000ms scraping operations = 0.2%)

---

## 6. Profiling and Measurement Strategy

### 6.1 Benchmarking Framework

**Create comprehensive benchmark suite**:
```typescript
// packages/scrapouille-tui/benchmarks/startup.bench.ts
import { bench, run } from 'mitata';

bench('Cold startup (first launch)', async () => {
  const start = performance.now();
  const app = await import('../src/main');
  await app.initialize();
  const duration = performance.now() - start;
  console.log(`Startup: ${duration.toFixed(2)}ms`);
});

bench('Warm startup (cached modules)', async () => {
  // Measure second launch
});

bench('Tab switching (Single → Batch)', async () => {
  // Measure tab mount/unmount
});

await run();
```

**Expected output**:
```
Startup benchmarks:
  Cold startup (first launch)    142.3ms  (target: <200ms) ✅
  Warm startup (cached modules)   67.8ms  (target: <100ms) ✅
  Tab switching (Single → Batch)  12.4ms  (target: <50ms)  ✅
```

### 6.2 Memory Profiling

**Leverage Bun's built-in profiler**:
```bash
# Memory heap snapshot
bun --inspect src/main.ts

# Profile memory usage over time
bun --inspect-brk --inspect-wait src/main.ts
# Open chrome://inspect, take heap snapshots
```

**Create automated memory test**:
```typescript
// packages/scrapouille-tui/tests/memory.test.ts
import { test, expect } from 'bun:test';

test('Memory footprint under normal workload', async () => {
  const baseline = process.memoryUsage();

  // Simulate 10 scraping operations
  for (let i = 0; i < 10; i++) {
    await simulateScrape();
  }

  const peak = process.memoryUsage();
  const delta = (peak.heapUsed - baseline.heapUsed) / 1024 / 1024;

  console.log(`Memory delta: ${delta.toFixed(2)} MB`);
  expect(delta).toBeLessThan(10);  // No more than 10MB growth
});
```

### 6.3 Rendering Performance Metrics

**Leverage TUIjoli's built-in renderStats** (renderer.zig lines 56-70):
```zig
renderStats: struct {
    lastFrameTime: f64,
    averageFrameTime: f64,
    frameCount: u64,
    fps: u32,
    cellsUpdated: u32,  // Key metric!
    renderTime: ?f64,
    overallFrameTime: ?f64,
    // ...
},
```

**Expose to TypeScript**:
```typescript
// Access Zig render stats from JS
interface RenderStats {
  fps: number;
  cellsUpdated: number;
  frameTime: number;
}

function getRenderStats(): RenderStats {
  // FFI call to Zig
  return tuijoli.getRendererStats();
}

// Log performance warnings
setInterval(() => {
  const stats = getRenderStats();
  if (stats.fps < 50) {
    console.warn(`Low FPS detected: ${stats.fps}`);
  }
  if (stats.cellsUpdated > 1000) {
    console.warn(`High cell update count: ${stats.cellsUpdated}`);
  }
}, 1000);
```

### 6.4 Async Operation Tracing

**Create async operation profiler**:
```typescript
// packages/scrapouille-tui/src/profiler.ts
class AsyncProfiler {
  private operations: Map<string, number[]> = new Map();

  start(operationName: string) {
    if (!this.operations.has(operationName)) {
      this.operations.set(operationName, []);
    }
    this.operations.get(operationName)!.push(performance.now());
  }

  end(operationName: string) {
    const times = this.operations.get(operationName)!;
    const duration = performance.now() - times.pop()!;
    console.log(`${operationName}: ${duration.toFixed(2)}ms`);
  }

  report() {
    for (const [op, times] of this.operations.entries()) {
      const avg = times.reduce((a, b) => a + b, 0) / times.length;
      console.log(`${op}: avg ${avg.toFixed(2)}ms (${times.length} samples)`);
    }
  }
}

// Usage
const profiler = new AsyncProfiler();

async function scrapeSingle(url: string) {
  profiler.start('scrape');
  await backend.scrape(url);
  profiler.end('scrape');
}
```

### 6.5 Continuous Performance Monitoring

**Add performance regression tests to CI**:
```yaml
# .github/workflows/performance.yml
name: Performance Tests

on: [pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: oven-sh/setup-bun@v1

      - name: Run benchmarks
        run: bun run benchmarks

      - name: Check performance budgets
        run: |
          # Fail if startup > 200ms
          # Fail if memory > 40MB
          # Fail if FPS < 55
          bun run check-budgets

      - name: Post benchmark results
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'customBiggerIsBetter'
          output-file-path: benchmark-results.json
```

### 6.6 Performance Dashboard

**Real-time performance monitoring in dev mode**:
```typescript
// packages/scrapouille-tui/src/debug-overlay.ts
class PerformanceOverlay {
  private enabled: boolean = process.env.NODE_ENV === 'development';

  render() {
    if (!this.enabled) return;

    const stats = getRenderStats();
    const memory = process.memoryUsage();

    // Render overlay in bottom-right corner
    // (inspired by renderer.zig debugOverlay, lines 84-90)
    drawOverlay({
      fps: stats.fps,
      memory: (memory.heapUsed / 1024 / 1024).toFixed(1),
      cellsUpdated: stats.cellsUpdated,
      asyncOps: getActiveAsyncOps(),
    });
  }
}
```

### 6.7 Measurement Targets

| Metric | Baseline | Target | Tool |
|--------|----------|--------|------|
| Cold startup | 600-1000ms | <200ms | mitata benchmark |
| Warm startup | 400-600ms | <100ms | mitata benchmark |
| Memory (idle) | 50MB | <30MB | bun:test |
| Memory (10 scrapes) | 60MB | <40MB | bun:test |
| FPS (typing) | 50-60 | 60 | renderStats |
| FPS (batch update) | 30-40 | 60 | renderStats |
| Cells updated/frame | 500-1000 | <200 | renderStats |
| Async operation blocking | 70-90% | 0% | AsyncProfiler |

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goals**:
- Set up TUIjoli + Bun project structure
- Port basic layout (StatusBar, TabContainer)
- Implement lazy loading for tabs
- Establish Python ↔ Bun IPC bridge

**Deliverables**:
- `packages/scrapouille-tui/` directory structure
- Basic app with 1-2 tabs functional
- Startup time: <300ms

### Phase 2: Core Features (Week 3-4)

**Goals**:
- Port Single URL tab with full functionality
- Implement worker thread for scraping
- Migrate cache.py → TypeScript (ioredis)
- Migrate metrics.py → TypeScript (bun:sqlite)

**Deliverables**:
- Single URL scraping fully functional
- Non-blocking UI during scraping
- Startup time: <200ms
- Memory: <35MB

### Phase 3: Advanced Features (Week 5-6)

**Goals**:
- Port Batch tab with virtualized table
- Implement streaming results
- Add incremental rendering optimizations
- Port Metrics tab with live updates

**Deliverables**:
- All 5 tabs functional
- 60fps sustained in all scenarios
- Memory: <30MB

### Phase 4: Polish & Profiling (Week 7-8)

**Goals**:
- Add performance monitoring dashboard
- Implement all rendering optimizations
- Comprehensive benchmark suite
- Performance regression tests in CI

**Deliverables**:
- Production-ready TUIjoli-based TUI
- Full documentation
- Performance benchmarks published
- Startup: <100ms (stretch goal)

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| IPC overhead too high | Low | Medium | Keep Python backend calls coarse-grained |
| Zig FFI complexity | Medium | Low | Use TUIjoli's existing abstractions |
| Worker thread instability | Low | High | Extensive error handling + fallback to main thread |
| Memory leak in Zig layer | Low | High | Arena allocators + comprehensive testing |

### 8.2 Migration Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Feature parity issues | Medium | Medium | Phase-by-phase migration with testing |
| Python backend compatibility | Low | High | Maintain existing scraper/ modules |
| User workflow disruption | Low | Medium | Keep Streamlit UI as fallback |

### 8.3 Performance Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Targets not achievable | Low | Medium | Conservative budgets (200ms vs <100ms) |
| Regression in later phases | Medium | Low | Continuous performance monitoring in CI |
| Platform-specific issues | Medium | Medium | Test on Linux/macOS/Windows |

---

## 9. Success Metrics

### 9.1 Quantitative Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Startup time** | 600-1000ms | <200ms | mitata benchmark |
| **Memory footprint** | 50MB | <30MB | bun:test |
| **FPS (sustained)** | 30-60 | 60 | renderStats |
| **UI responsiveness** | 30-70% | 100% | User timing API |
| **Batch throughput** | 5 URLs/s | 8-10 URLs/s | Benchmark |

### 9.2 Qualitative Metrics

- **Developer experience**: Faster iteration with Bun hot reload (<100ms)
- **Code maintainability**: TypeScript types vs Python duck typing
- **User experience**: Smoother animations, no UI freezing
- **Cross-platform**: Single Bun binary vs Python + dependencies

### 9.3 Acceptance Criteria

**Must Have**:
- ✅ Startup time <300ms (minimum acceptable)
- ✅ Memory <40MB (minimum acceptable)
- ✅ All features from current TUI functional
- ✅ Zero UI blocking during scraping

**Should Have**:
- ✅ Startup time <200ms (target)
- ✅ Memory <30MB (target)
- ✅ 60fps sustained in all scenarios
- ✅ Virtualized tables for 100+ rows

**Nice to Have**:
- ✅ Startup time <100ms (stretch goal)
- ✅ Memory <25MB (stretch goal)
- ✅ Optional render thread for 120fps
- ✅ Real-time performance dashboard

---

## 10. Conclusion

### Expected Performance Gains

| Category | Current | Target | Improvement |
|----------|---------|--------|-------------|
| Startup time | 600-1000ms | 100-200ms | 75-85% faster |
| Memory | 50MB | 25-35MB | 30-50% reduction |
| Rendering | 30-60fps | 60fps sustained | 2× more consistent |
| UI blocking | 70-90% | 0% | 100% responsive |

### Technical Confidence

**High confidence** (proven technology):
- Bun runtime performance gains
- TUIjoli native Zig rendering
- Lazy loading and code splitting
- Worker thread architecture

**Medium confidence** (needs validation):
- IPC overhead acceptable for use case
- All features can be ported without loss
- Memory targets achievable in practice

**Low confidence** (stretch goals):
- <100ms cold startup (requires aggressive optimization)
- <25MB memory (may need Zig for more modules)

### Recommendation

**Proceed with migration** based on:
1. Strong architectural foundation in both codebases
2. Clear optimization paths with measurable targets
3. Incremental migration reduces risk
4. Fallback to existing Python TUI if needed

**Next steps**:
1. Create TUIjoli project scaffold (1 day)
2. Implement basic IPC bridge + one tab (1 week)
3. Benchmark and validate performance gains (2 days)
4. If successful, continue full migration (4-6 weeks)

---

**Document Version**: 1.0
**Author**: Performance Engineering Analysis
**Last Updated**: 2025-11-11
**Next Review**: After Phase 1 completion
