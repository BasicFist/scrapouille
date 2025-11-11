# TUIjoli Architecture: Code Examples & Patterns

**Companion to**: TUIJOLI-PERFORMANCE-OPTIMIZATION.md
**Focus**: Concrete implementation patterns with code examples
**Date**: 2025-11-11

---

## 1. Project Structure

```
scrapouille/
├── packages/
│   ├── scrapouille-tui/              # New TUIjoli-based TUI
│   │   ├── src/
│   │   │   ├── main.ts               # Entry point (lazy loading)
│   │   │   ├── app.ts                # Main application class
│   │   │   ├── backend-bridge.ts     # Python ↔ Bun IPC
│   │   │   ├── components/
│   │   │   │   ├── status-bar.ts
│   │   │   │   ├── metrics-panel.ts
│   │   │   │   └── progress-bar.ts
│   │   │   ├── tabs/
│   │   │   │   ├── single-url.ts     # Lazy loaded
│   │   │   │   ├── batch.ts          # Lazy loaded
│   │   │   │   ├── metrics.ts        # Lazy loaded
│   │   │   │   ├── config.ts         # Lazy loaded
│   │   │   │   └── help.ts           # Lazy loaded
│   │   │   ├── backend/
│   │   │   │   ├── cache.ts          # Ported from cache.py
│   │   │   │   ├── metrics-db.ts     # Ported from metrics.py
│   │   │   │   └── scraping-worker.ts # Worker thread
│   │   │   ├── utils/
│   │   │   │   ├── profiler.ts       # Performance monitoring
│   │   │   │   └── debug-overlay.ts  # Dev mode overlay
│   │   │   └── types.ts               # TypeScript definitions
│   │   ├── benchmarks/
│   │   │   ├── startup.bench.ts
│   │   │   ├── memory.bench.ts
│   │   │   └── rendering.bench.ts
│   │   ├── tests/
│   │   │   ├── memory.test.ts
│   │   │   └── integration.test.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── core/                          # TUIjoli (existing)
│       └── src/zig/                   # Native Zig layer
│
├── scraper/                           # Existing Python backend (keep)
│   ├── batch.py
│   ├── cache.py
│   ├── metrics.py
│   └── ...
│
├── tui.py                             # Old Textual TUI (deprecate)
├── scraper.py                         # Streamlit UI (keep as fallback)
└── ...
```

---

## 2. Entry Point: Lazy Loading

### main.ts (Minimal Cold Start)

```typescript
#!/usr/bin/env bun
/**
 * Scrapouille TUI - Main Entry Point
 * Target: <100ms to first interactive paint
 */

// TIER 1: Critical imports only (<50ms)
import { TUIjoli } from '@tuijoli/core';
import { StatusBar } from './components/status-bar';
import { TabContainer } from './components/tab-container';

// TIER 2: Deferred heavy imports
let SingleURLTab: any;
let BatchTab: any;
let MetricsTab: any;
let ConfigTab: any;
let HelpTab: any;

async function loadTabs() {
  // Load tabs in background (non-blocking)
  [SingleURLTab, BatchTab, MetricsTab, ConfigTab, HelpTab] = await Promise.all([
    import('./tabs/single-url'),
    import('./tabs/batch'),
    import('./tabs/metrics'),
    import('./tabs/config'),
    import('./tabs/help'),
  ]);
}

async function main() {
  const startTime = performance.now();

  // Initialize TUIjoli with minimal components
  const app = new TUIjoli({
    title: 'Scrapouille v3.0 - AI-Powered Web Scraper',
    width: process.stdout.columns,
    height: process.stdout.rows,
    components: [
      new StatusBar({ id: 'status-bar' }),
      new TabContainer({ id: 'tab-container' }),
    ],
  });

  // Render immediately (target: <100ms)
  await app.mount();
  const mountTime = performance.now() - startTime;
  console.log(`✓ App mounted in ${mountTime.toFixed(2)}ms`);

  // Load tabs in background
  loadTabs().then(() => {
    const totalTime = performance.now() - startTime;
    console.log(`✓ All tabs loaded in ${totalTime.toFixed(2)}ms`);

    // Register tabs dynamically
    app.registerTabs([
      { name: 'Single URL', component: SingleURLTab },
      { name: 'Batch', component: BatchTab },
      { name: 'Metrics', component: MetricsTab },
      { name: 'Config', component: ConfigTab },
      { name: 'Help', component: HelpTab },
    ]);
  });

  // Handle Ctrl+Q to quit
  process.on('SIGINT', () => {
    app.unmount();
    process.exit(0);
  });
}

// Run immediately
main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
```

---

## 3. Backend Bridge: Bun ↔ Python IPC

### backend-bridge.ts

```typescript
/**
 * IPC Bridge between Bun (TUI) and Python (scraper backend)
 * Uses Bun's native subprocess IPC for low overhead
 */

import { spawn, type Subprocess } from 'bun';
import type { ScrapeRequest, ScrapeResult } from './types';

export class PythonBackend {
  private process: Subprocess;
  private requestId: number = 0;
  private pendingRequests: Map<
    number,
    { resolve: (value: any) => void; reject: (error: any) => void }
  > = new Map();

  constructor() {
    // Start Python backend as subprocess with IPC
    this.process = spawn({
      cmd: [
        'python',
        '-m',
        'scraper.ipc_server',  // New IPC server script
      ],
      cwd: process.cwd(),
      env: process.env,
      stdout: 'pipe',
      stdin: 'pipe',
      ipc: (message) => this.handleMessage(message),
    });

    // Handle process errors
    this.process.on('error', (err) => {
      console.error('Python backend error:', err);
    });

    console.log('✓ Python backend started (PID:', this.process.pid, ')');
  }

  private handleMessage(message: any) {
    const { requestId, type, data, error } = message;

    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      console.warn('Received response for unknown request:', requestId);
      return;
    }

    this.pendingRequests.delete(requestId);

    if (type === 'success') {
      pending.resolve(data);
    } else if (type === 'error') {
      pending.reject(new Error(error));
    } else if (type === 'progress') {
      // Handle progress updates (don't resolve yet)
      // TODO: Implement progress callback mechanism
    }
  }

  private sendRequest(method: string, params: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;
      this.pendingRequests.set(requestId, { resolve, reject });

      this.process.send({
        requestId,
        method,
        params,
      });
    });
  }

  async scrapeSingle(request: ScrapeRequest): Promise<ScrapeResult> {
    return this.sendRequest('scrape_single', request);
  }

  async scrapeBatch(requests: ScrapeRequest[]): Promise<ScrapeResult[]> {
    return this.sendRequest('scrape_batch', requests);
  }

  async getMetricsStats(days: number): Promise<any> {
    return this.sendRequest('get_metrics_stats', { days });
  }

  async checkOllamaConnection(): Promise<boolean> {
    try {
      const result = await this.sendRequest('check_ollama', {});
      return result.connected;
    } catch {
      return false;
    }
  }

  async shutdown() {
    this.process.kill();
  }
}

// Singleton instance
let backendInstance: PythonBackend | null = null;

export function getBackend(): PythonBackend {
  if (!backendInstance) {
    backendInstance = new PythonBackend();
  }
  return backendInstance;
}
```

### scraper/ipc_server.py (New Python IPC Server)

```python
"""
IPC server for Scrapouille backend
Receives commands via stdin, sends responses via stdout
"""
import sys
import json
import asyncio
from scraper.tui_integration import TUIScraperBackend

backend = TUIScraperBackend()

async def handle_request(request):
    """Handle a single IPC request"""
    request_id = request['requestId']
    method = request['method']
    params = request['params']

    try:
        if method == 'scrape_single':
            result, metadata = await backend.scrape_single_url(**params)
            response = {
                'requestId': request_id,
                'type': 'success',
                'data': {'result': result, 'metadata': metadata}
            }

        elif method == 'scrape_batch':
            results = await backend.scrape_batch(**params)
            response = {
                'requestId': request_id,
                'type': 'success',
                'data': [r.to_dict() for r in results]
            }

        elif method == 'get_metrics_stats':
            stats = backend.get_metrics_stats(**params)
            response = {
                'requestId': request_id,
                'type': 'success',
                'data': stats
            }

        elif method == 'check_ollama':
            connected = await backend.check_ollama_connection()
            response = {
                'requestId': request_id,
                'type': 'success',
                'data': {'connected': connected}
            }

        else:
            raise ValueError(f"Unknown method: {method}")

    except Exception as e:
        response = {
            'requestId': request_id,
            'type': 'error',
            'error': str(e)
        }

    # Send response back to Bun
    sys.stdout.write(json.dumps(response) + '\n')
    sys.stdout.flush()

async def main():
    """Main IPC loop"""
    # Read requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            await handle_request(request)
        except Exception as e:
            sys.stderr.write(f"Error processing request: {e}\n")

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 4. Worker Thread for Scraping

### scraping-worker.ts

```typescript
/**
 * Dedicated worker thread for scraping operations
 * Keeps main thread (UI) responsive at 60fps
 */

import { Worker } from 'bun';
import type { ScrapeRequest, ScrapeResult } from './types';

export class ScrapingWorker {
  private worker: Worker;
  private taskId: number = 0;
  private pendingTasks: Map<
    number,
    {
      resolve: (value: ScrapeResult) => void;
      reject: (error: any) => void;
      progressCallback?: (done: number, total: number) => void;
    }
  > = new Map();

  constructor() {
    // Create worker from separate file
    this.worker = new Worker(new URL('./worker-impl.ts', import.meta.url));

    // Handle messages from worker
    this.worker.onmessage = (event) => {
      const { taskId, type, data, error } = event.data;

      const task = this.pendingTasks.get(taskId);
      if (!task) return;

      if (type === 'progress' && task.progressCallback) {
        task.progressCallback(data.done, data.total);
      } else if (type === 'result') {
        this.pendingTasks.delete(taskId);
        task.resolve(data);
      } else if (type === 'error') {
        this.pendingTasks.delete(taskId);
        task.reject(new Error(error));
      }
    };

    console.log('✓ Scraping worker initialized');
  }

  async scrapeSingle(
    request: ScrapeRequest,
    progressCallback?: (done: number, total: number) => void
  ): Promise<ScrapeResult> {
    return new Promise((resolve, reject) => {
      const taskId = ++this.taskId;
      this.pendingTasks.set(taskId, { resolve, reject, progressCallback });

      this.worker.postMessage({
        taskId,
        type: 'scrape_single',
        request,
      });
    });
  }

  async scrapeBatch(
    requests: ScrapeRequest[],
    progressCallback?: (done: number, total: number) => void
  ): Promise<ScrapeResult[]> {
    return new Promise((resolve, reject) => {
      const taskId = ++this.taskId;
      this.pendingTasks.set(taskId, { resolve, reject, progressCallback });

      this.worker.postMessage({
        taskId,
        type: 'scrape_batch',
        requests,
      });
    });
  }

  terminate() {
    this.worker.terminate();
  }
}
```

### worker-impl.ts (Worker Thread Implementation)

```typescript
/**
 * Worker thread implementation
 * Runs in separate thread, communicates via postMessage
 */

import { getBackend } from './backend-bridge';

const backend = getBackend();

self.onmessage = async (event) => {
  const { taskId, type, request, requests } = event.data;

  try {
    if (type === 'scrape_single') {
      // Scrape in worker thread (non-blocking UI)
      const result = await backend.scrapeSingle(request);

      self.postMessage({
        taskId,
        type: 'result',
        data: result,
      });
    } else if (type === 'scrape_batch') {
      let completed = 0;
      const results: any[] = [];

      for (const req of requests) {
        const result = await backend.scrapeSingle(req);
        results.push(result);
        completed++;

        // Send progress update
        self.postMessage({
          taskId,
          type: 'progress',
          data: { done: completed, total: requests.length },
        });
      }

      // Send final results
      self.postMessage({
        taskId,
        type: 'result',
        data: results,
      });
    }
  } catch (error: any) {
    self.postMessage({
      taskId,
      type: 'error',
      error: error.message,
    });
  }
};
```

---

## 5. Native Cache Implementation

### cache.ts (Ported from cache.py)

```typescript
/**
 * Redis-based caching for scraping results
 * Ported from scraper/cache.py for native performance
 */

import { Redis } from 'ioredis';
import { createHash } from 'crypto';

export class ScraperCache {
  private client: Redis | null = null;
  private enabled: boolean;
  private defaultTTL: number;

  constructor(config: {
    host?: string;
    port?: number;
    db?: number;
    enabled?: boolean;
    defaultTTLHours?: number;
  } = {}) {
    this.enabled = config.enabled ?? true;
    this.defaultTTL = (config.defaultTTLHours ?? 24) * 3600;

    if (!this.enabled) {
      console.log('Cache disabled');
      return;
    }

    try {
      this.client = new Redis({
        host: config.host ?? 'localhost',
        port: config.port ?? 6379,
        db: config.db ?? 0,
        lazyConnect: true,  // Connect on first use
        maxRetriesPerRequest: 3,
        enableReadyCheck: true,
        enableAutoPipelining: true,  // Batch commands for performance
      });

      // Test connection
      this.client.connect().then(() => {
        console.log(`✓ Connected to Redis at ${config.host}:${config.port}`);
      });
    } catch (err) {
      console.warn('Redis connection failed:', err, '. Cache disabled.');
      this.client = null;
      this.enabled = false;
    }
  }

  private makeKey(url: string, prompt: string, extras: Record<string, any> = {}): string {
    // Deterministic hash of URL + prompt + extras
    const keyData = JSON.stringify({ url, prompt, ...extras }, Object.keys({ url, prompt, ...extras }).sort());
    const hash = createHash('sha256').update(keyData).digest('hex').slice(0, 16);
    return `scrape:${hash}`;
  }

  async get(url: string, prompt: string, extras?: Record<string, any>): Promise<any | null> {
    if (!this.enabled || !this.client) return null;

    try {
      const key = this.makeKey(url, prompt, extras);
      const cached = await this.client.get(key);

      if (cached) {
        console.log(`✓ Cache HIT: ${key}`);
        return JSON.parse(cached);
      } else {
        console.log(`✗ Cache MISS: ${key}`);
        return null;
      }
    } catch (err) {
      console.error('Cache GET error:', err);
      return null;
    }
  }

  async set(
    url: string,
    prompt: string,
    data: any,
    ttlHours?: number,
    extras?: Record<string, any>
  ): Promise<void> {
    if (!this.enabled || !this.client) return;

    try {
      const key = this.makeKey(url, prompt, extras);
      const ttl = (ttlHours ?? this.defaultTTL / 3600) * 3600;

      await this.client.setex(key, ttl, JSON.stringify(data));
      console.log(`✓ Cache SET: ${key} (TTL: ${ttl}s)`);
    } catch (err) {
      console.error('Cache SET error:', err);
    }
  }

  async clear(): Promise<void> {
    if (!this.enabled || !this.client) return;

    try {
      const keys = await this.client.keys('scrape:*');
      if (keys.length > 0) {
        await this.client.del(...keys);
        console.log(`✓ Cleared ${keys.length} cache entries`);
      }
    } catch (err) {
      console.error('Cache CLEAR error:', err);
    }
  }

  async getStats(): Promise<{ totalKeys: number; hitRate: number }> {
    if (!this.enabled || !this.client) {
      return { totalKeys: 0, hitRate: 0 };
    }

    try {
      const keys = await this.client.keys('scrape:*');
      // Hit rate tracking would require additional metadata
      return { totalKeys: keys.length, hitRate: 0 };
    } catch (err) {
      console.error('Cache STATS error:', err);
      return { totalKeys: 0, hitRate: 0 };
    }
  }

  async disconnect() {
    if (this.client) {
      await this.client.quit();
    }
  }
}
```

---

## 6. Native Metrics Database

### metrics-db.ts (Ported from metrics.py)

```typescript
/**
 * SQLite-based metrics persistence
 * Ported from scraper/metrics.py for native performance
 */

import { Database } from 'bun:sqlite';
import { createHash } from 'crypto';

export interface ScrapeMetric {
  id?: number;
  timestamp: string;
  url: string;
  promptHash: string;
  model: string;
  executionTimeSeconds: number;
  tokenCount?: number;
  retryCount: number;
  fallbackAttempts: number;
  cached: boolean;
  validationPassed: boolean;
  schemaUsed?: string;
  error?: string;
}

export class MetricsDB {
  private db: Database;

  constructor(dbPath: string = 'data/metrics.db') {
    this.db = new Database(dbPath, { create: true });
    this.initSchema();
    console.log(`✓ Metrics DB initialized: ${dbPath}`);
  }

  private initSchema() {
    // Create table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS scrapes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        url TEXT NOT NULL,
        prompt_hash TEXT NOT NULL,
        model TEXT NOT NULL,
        execution_time_seconds REAL NOT NULL,
        token_count INTEGER,
        retry_count INTEGER DEFAULT 0,
        fallback_attempts INTEGER DEFAULT 1,
        cached BOOLEAN DEFAULT 0,
        validation_passed BOOLEAN DEFAULT 1,
        schema_used TEXT,
        error TEXT
      )
    `);

    // Create indexes
    this.db.run('CREATE INDEX IF NOT EXISTS idx_timestamp ON scrapes(timestamp)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_url ON scrapes(url)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_model ON scrapes(model)');
  }

  logScrape(params: {
    url: string;
    prompt: string;
    model: string;
    executionTime: number;
    tokenCount?: number;
    retryCount?: number;
    fallbackAttempts?: number;
    cached?: boolean;
    validationPassed?: boolean;
    schemaUsed?: string;
    error?: string;
  }): number {
    // Hash prompt for privacy
    const promptHash = createHash('sha256').update(params.prompt).digest('hex').slice(0, 16);

    const stmt = this.db.prepare(`
      INSERT INTO scrapes (
        timestamp, url, prompt_hash, model, execution_time_seconds,
        token_count, retry_count, fallback_attempts, cached,
        validation_passed, schema_used, error
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      new Date().toISOString(),
      params.url,
      promptHash,
      params.model,
      params.executionTime,
      params.tokenCount ?? null,
      params.retryCount ?? 0,
      params.fallbackAttempts ?? 1,
      params.cached ? 1 : 0,
      params.validationPassed ? 1 : 0,
      params.schemaUsed ?? null,
      params.error ?? null
    );

    return result.lastInsertRowid as number;
  }

  getRecent(limit: number = 100): ScrapeMetric[] {
    const stmt = this.db.prepare(`
      SELECT * FROM scrapes
      ORDER BY timestamp DESC
      LIMIT ?
    `);

    return stmt.all(limit) as ScrapeMetric[];
  }

  getStats(days: number = 7): {
    totalScrapes: number;
    avgTime: number;
    cacheHitRate: number;
    errorRate: number;
    modelUsage: Record<string, number>;
  } {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    // Total scrapes
    const totalStmt = this.db.prepare(`
      SELECT COUNT(*) as count FROM scrapes
      WHERE timestamp > ?
    `);
    const totalScrapes = (totalStmt.get(cutoff.toISOString()) as any).count;

    // Average time
    const avgStmt = this.db.prepare(`
      SELECT AVG(execution_time_seconds) as avg FROM scrapes
      WHERE timestamp > ?
    `);
    const avgTime = (avgStmt.get(cutoff.toISOString()) as any).avg ?? 0;

    // Cache hit rate
    const cacheStmt = this.db.prepare(`
      SELECT
        SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as hits,
        COUNT(*) as total
      FROM scrapes
      WHERE timestamp > ?
    `);
    const cacheData = cacheStmt.get(cutoff.toISOString()) as any;
    const cacheHitRate = cacheData.total > 0 ? (cacheData.hits / cacheData.total) * 100 : 0;

    // Error rate
    const errorStmt = this.db.prepare(`
      SELECT
        SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
        COUNT(*) as total
      FROM scrapes
      WHERE timestamp > ?
    `);
    const errorData = errorStmt.get(cutoff.toISOString()) as any;
    const errorRate = errorData.total > 0 ? (errorData.errors / errorData.total) * 100 : 0;

    // Model usage
    const modelStmt = this.db.prepare(`
      SELECT model, COUNT(*) as count
      FROM scrapes
      WHERE timestamp > ?
      GROUP BY model
    `);
    const modelRows = modelStmt.all(cutoff.toISOString()) as any[];
    const modelUsage: Record<string, number> = {};
    for (const row of modelRows) {
      modelUsage[row.model] = row.count;
    }

    return {
      totalScrapes,
      avgTime,
      cacheHitRate,
      errorRate,
      modelUsage,
    };
  }

  close() {
    this.db.close();
  }
}
```

---

## 7. Performance Profiler

### profiler.ts

```typescript
/**
 * Lightweight performance profiler for Scrapouille
 * Tracks operation timings and memory usage
 */

export class Profiler {
  private operations: Map<string, { times: number[]; memory: number[] }> = new Map();
  private activeTimers: Map<string, number> = new Map();

  start(operationName: string) {
    this.activeTimers.set(operationName, performance.now());

    if (!this.operations.has(operationName)) {
      this.operations.set(operationName, { times: [], memory: [] });
    }
  }

  end(operationName: string) {
    const startTime = this.activeTimers.get(operationName);
    if (!startTime) {
      console.warn(`Timer not found for operation: ${operationName}`);
      return;
    }

    const duration = performance.now() - startTime;
    const memoryUsage = process.memoryUsage().heapUsed / 1024 / 1024; // MB

    const data = this.operations.get(operationName)!;
    data.times.push(duration);
    data.memory.push(memoryUsage);

    this.activeTimers.delete(operationName);

    console.log(`[Profiler] ${operationName}: ${duration.toFixed(2)}ms`);
  }

  report() {
    console.log('\n=== Performance Report ===\n');

    for (const [operation, data] of this.operations.entries()) {
      const avgTime = data.times.reduce((a, b) => a + b, 0) / data.times.length;
      const minTime = Math.min(...data.times);
      const maxTime = Math.max(...data.times);
      const avgMemory = data.memory.reduce((a, b) => a + b, 0) / data.memory.length;

      console.log(`${operation}:`);
      console.log(`  Time:   avg ${avgTime.toFixed(2)}ms, min ${minTime.toFixed(2)}ms, max ${maxTime.toFixed(2)}ms`);
      console.log(`  Memory: avg ${avgMemory.toFixed(2)} MB`);
      console.log(`  Samples: ${data.times.length}`);
      console.log();
    }
  }

  clear() {
    this.operations.clear();
    this.activeTimers.clear();
  }
}

// Singleton instance
export const profiler = new Profiler();
```

---

## 8. Benchmark Suite

### startup.bench.ts

```typescript
/**
 * Startup time benchmarks
 * Target: <200ms cold start, <100ms warm start
 */

import { bench, run } from 'mitata';

bench('Cold startup (first launch)', async () => {
  // Simulate cold start (no module cache)
  const start = performance.now();

  // Dynamic import to avoid caching
  const { main } = await import('../src/main?t=' + Date.now());
  await main();

  const duration = performance.now() - start;
  console.log(`Cold startup: ${duration.toFixed(2)}ms`);

  if (duration > 200) {
    console.warn('⚠️  Cold startup exceeded target (200ms)');
  }
});

bench('Warm startup (cached modules)', async () => {
  const start = performance.now();

  // Import with cache
  const { main } = await import('../src/main');
  await main();

  const duration = performance.now() - start;
  console.log(`Warm startup: ${duration.toFixed(2)}ms`);

  if (duration > 100) {
    console.warn('⚠️  Warm startup exceeded target (100ms)');
  }
});

bench('Tab switching (Single → Batch)', async () => {
  const { TabManager } = await import('../src/components/tab-manager');
  const manager = new TabManager();

  const start = performance.now();
  await manager.switchTab('batch');
  const duration = performance.now() - start;

  console.log(`Tab switch: ${duration.toFixed(2)}ms`);

  if (duration > 50) {
    console.warn('⚠️  Tab switching exceeded target (50ms)');
  }
});

// Run benchmarks
await run();
```

### memory.bench.ts

```typescript
/**
 * Memory usage benchmarks
 * Target: <40MB under normal workload
 */

import { test, expect } from 'bun:test';

test('Baseline memory usage', () => {
  const baseline = process.memoryUsage();
  console.log('Baseline memory:', {
    heapUsed: (baseline.heapUsed / 1024 / 1024).toFixed(2) + ' MB',
    heapTotal: (baseline.heapTotal / 1024 / 1024).toFixed(2) + ' MB',
    rss: (baseline.rss / 1024 / 1024).toFixed(2) + ' MB',
  });

  // Baseline should be <30MB
  expect(baseline.heapUsed / 1024 / 1024).toBeLessThan(30);
});

test('Memory under normal workload (10 scrapes)', async () => {
  const { getBackend } = await import('../src/backend-bridge');
  const backend = getBackend();

  const baseline = process.memoryUsage();

  // Simulate 10 scraping operations
  for (let i = 0; i < 10; i++) {
    await backend.scrapeSingle({
      url: 'https://example.com',
      prompt: 'Extract title',
      model: 'qwen2.5-coder:7b',
    });
  }

  const peak = process.memoryUsage();
  const delta = (peak.heapUsed - baseline.heapUsed) / 1024 / 1024;

  console.log('Memory delta:', delta.toFixed(2) + ' MB');

  // Should not grow by more than 10MB
  expect(delta).toBeLessThan(10);
});

test('Memory after tab unmount', async () => {
  const { TabManager } = await import('../src/components/tab-manager');
  const manager = new TabManager();

  // Mount and unmount tab
  await manager.switchTab('single-url');
  const beforeUnmount = process.memoryUsage();

  await manager.switchTab('batch');
  const afterUnmount = process.memoryUsage();

  // Force GC if available
  if (global.gc) {
    global.gc();
  }

  const delta = (afterUnmount.heapUsed - beforeUnmount.heapUsed) / 1024 / 1024;

  console.log('Memory after unmount:', delta.toFixed(2) + ' MB');

  // Should free memory (negative delta or minimal growth)
  expect(delta).toBeLessThan(5);
});
```

---

## 9. Summary: Key Patterns

### Pattern 1: Lazy Loading
```typescript
// ✅ Good: Defer heavy imports
async function loadHeavyModule() {
  return await import('./heavy-module');
}

// ❌ Bad: Load everything upfront
import { HeavyModule } from './heavy-module';
```

### Pattern 2: Worker Threads
```typescript
// ✅ Good: Offload to worker
const worker = new Worker('./worker.ts');
worker.postMessage({ type: 'scrape', url });

// ❌ Bad: Block main thread
await expensiveScraping(url);
```

### Pattern 3: Incremental Rendering
```typescript
// ✅ Good: Batch updates
component.updateAll({ field1, field2, field3 });

// ❌ Bad: Individual updates
component.field1 = value1;
component.field2 = value2;
component.field3 = value3;
```

### Pattern 4: Native Backend
```typescript
// ✅ Good: Native Bun SQLite
const db = new Database('data.db');
db.prepare('SELECT * FROM users').all();

// ❌ Bad: IPC to Python for simple queries
await pythonBackend.query('SELECT * FROM users');
```

### Pattern 5: Memory Management
```typescript
// ✅ Good: Unmount inactive components
tabManager.unmountInactiveTabs();

// ❌ Bad: Keep all components in memory
tabManager.keepAllTabsMounted();
```

---

**Next Steps**:
1. Review TUIJOLI-PERFORMANCE-OPTIMIZATION.md for full analysis
2. Start with Phase 1: Foundation (main.ts + basic IPC)
3. Measure baseline performance with benchmarks
4. Iterate on optimizations based on profiler data

**Documentation Version**: 1.0
**Last Updated**: 2025-11-11
