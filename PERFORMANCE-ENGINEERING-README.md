# Performance Engineering: TUIjoli Migration

**Navigation guide for performance optimization documentation**

---

## Overview

This directory contains comprehensive performance engineering analysis for migrating Scrapouille's Terminal UI from Python/Textual to TUIjoli's Bun + native Zig architecture.

**Current State**: Production-ready v3.0 Phase 4 (Python/Textual)
**Target State**: v4.0 (Bun + TUIjoli with Zig rendering)

**Expected Gains**:
- **75-85% faster startup** (600-1000ms → 100-200ms)
- **30-50% less memory** (50MB → 25-35MB)
- **100% UI responsiveness** (0% blocking during scraping)
- **60fps sustained rendering** (vs 30-60fps variable)

---

## Documents in This Series

### 1. [TUIJOLI-PERFORMANCE-OPTIMIZATION.md](./TUIJOLI-PERFORMANCE-OPTIMIZATION.md)
**34KB, comprehensive analysis**

**Purpose**: Main performance optimization strategy document

**Contents**:
- Executive summary with performance targets
- 6 optimization categories with detailed analysis
- Risk assessment and mitigation strategies
- 8-week implementation roadmap
- Success metrics and acceptance criteria

**Key Sections**:
1. **Startup Optimization** - Lazy loading, Bun advantages, connection deferral
2. **Memory Optimization** - Component lifecycle, Zig buffers, state management
3. **Rendering Performance** - Native rendering, incremental updates, virtualization
4. **Async Operations** - Worker threads, non-blocking UI, streaming results
5. **Backend Integration** - IPC bridge patterns, native cache/metrics
6. **Profiling Strategy** - Benchmarking framework, continuous monitoring

**Read if**: You want comprehensive understanding of optimization techniques

---

### 2. [TUIJOLI-ARCHITECTURE-EXAMPLES.md](./TUIJOLI-ARCHITECTURE-EXAMPLES.md)
**29KB, code-focused guide**

**Purpose**: Concrete implementation patterns with runnable code examples

**Contents**:
- Project structure and file organization
- Complete code examples for all major components
- Design patterns and anti-patterns
- Worker thread implementations
- Native backend ports (cache, metrics)
- Performance profiler implementation

**Key Sections**:
1. **Project Structure** - Directory layout, file organization
2. **Entry Point** - Lazy loading pattern (main.ts)
3. **Backend Bridge** - Bun ↔ Python IPC implementation
4. **Worker Threads** - Scraping worker pattern
5. **Native Backends** - TypeScript ports of cache.py and metrics.py
6. **Profiler** - Performance monitoring implementation
7. **Benchmarks** - Complete benchmark suite code
8. **Summary Patterns** - Quick reference for key patterns

**Read if**: You're implementing the migration and need code examples

---

### 3. [PERFORMANCE-BENCHMARKS.md](./PERFORMANCE-BENCHMARKS.md)
**18KB, measurement methodology**

**Purpose**: Detailed benchmarks with measurement methods and expected results

**Contents**:
- Baseline measurements for current implementation
- Target performance metrics with test methodology
- Real-world use case benchmarks
- CI/CD integration for performance regression testing
- Performance validation checklist

**Key Sections**:
1. **Startup Performance** - Cold/warm startup, tab switching
2. **Memory Performance** - Idle, active workload, leak testing
3. **Rendering Performance** - FPS, frame time consistency, cell updates
4. **Async Operations** - UI responsiveness, progress latency, throughput
5. **Backend Integration** - IPC overhead, cache/metrics performance
6. **Real-World Use Cases** - Single scrape, batch processing, metrics view
7. **Measurement Automation** - CI/CD integration, continuous monitoring
8. **Performance Targets** - Must-have, should-have, stretch goals
9. **Validation Checklist** - Success criteria before v4.0 release

**Read if**: You need to measure and validate performance improvements

---

## Quick Start Guide

### For Understanding the Migration

**Read in this order**:
1. **Executive Summary** - TUIJOLI-PERFORMANCE-OPTIMIZATION.md (first 2 pages)
2. **Expected Gains Table** - PERFORMANCE-BENCHMARKS.md (first page)
3. **Key Patterns Summary** - TUIJOLI-ARCHITECTURE-EXAMPLES.md (last section)

**Time investment**: 15 minutes
**Outcome**: High-level understanding of what we're doing and why

---

### For Implementing Phase 1 (Foundation)

**Read in this order**:
1. **Startup Optimization** - TUIJOLI-PERFORMANCE-OPTIMIZATION.md (Section 1)
2. **Project Structure** - TUIJOLI-ARCHITECTURE-EXAMPLES.md (Section 1)
3. **Entry Point** - TUIJOLI-ARCHITECTURE-EXAMPLES.md (Section 2)
4. **Backend Bridge** - TUIJOLI-ARCHITECTURE-EXAMPLES.md (Section 3)
5. **Startup Benchmarks** - PERFORMANCE-BENCHMARKS.md (Section 1)

**Time investment**: 45 minutes
**Outcome**: Ready to implement basic TUIjoli app with IPC

---

### For Optimizing Performance

**Read in this order**:
1. **Performance Profiler** - TUIJOLI-ARCHITECTURE-EXAMPLES.md (Section 7)
2. **Measurement Automation** - PERFORMANCE-BENCHMARKS.md (Section 7)
3. **Rendering Performance** - TUIJOLI-PERFORMANCE-OPTIMIZATION.md (Section 3)
4. **Memory Optimization** - TUIJOLI-PERFORMANCE-OPTIMIZATION.md (Section 2)
5. **Async Operations** - TUIJOLI-PERFORMANCE-OPTIMIZATION.md (Section 4)

**Time investment**: 60 minutes
**Outcome**: Ready to profile and optimize bottlenecks

---

## Key Concepts Explained

### Lazy Loading
**Problem**: Loading all 5 tabs on startup takes 600-1000ms
**Solution**: Load only StatusBar + TabContainer initially, defer tab loading
**Code**: See TUIJOLI-ARCHITECTURE-EXAMPLES.md, Section 2 (main.ts)
**Gain**: 600-1000ms → 100-200ms startup

### Worker Threads
**Problem**: UI blocks 70-90% during 5-second scraping operations
**Solution**: Offload scraping to Bun Worker, keep main thread at 60fps
**Code**: See TUIJOLI-ARCHITECTURE-EXAMPLES.md, Section 4 (scraping-worker.ts)
**Gain**: 0% UI blocking (from 70-90%)

### IPC Bridge
**Problem**: Need to communicate between Bun (UI) and Python (backend)
**Solution**: Use Bun's native subprocess IPC with <5ms overhead
**Code**: See TUIJOLI-ARCHITECTURE-EXAMPLES.md, Section 3 (backend-bridge.ts)
**Overhead**: 0.02-0.2% of 5-second scraping operations (negligible)

### Native Rendering
**Problem**: Python → Textual → ANSI strings has high overhead
**Solution**: TypeScript → Zig (native) → ANSI strings, direct buffer access
**Code**: Leverage TUIjoli's renderer.zig (packages/core/src/zig/renderer.zig)
**Gain**: 60fps sustained, 5-15× fewer cell updates

### Incremental Rendering
**Problem**: Full screen re-render on every state change
**Solution**: Zig renderer tracks dirty cells, only writes changed cells
**Code**: Built into TUIjoli (renderer.zig, lines ~98-130)
**Gain**: 50-80% reduction in terminal writes

### Virtualization
**Problem**: Rendering 100-row table updates 6000 cells per frame (slow)
**Solution**: Render only visible rows in viewport
**Code**: Inspired by TUIjoli's text-buffer-view.zig
**Gain**: 90% reduction for 100+ row tables

---

## Performance Targets at a Glance

### Must-Have (Minimum Acceptance)
- ✅ Startup < 300ms
- ✅ Memory < 40MB
- ✅ FPS ≥ 50fps sustained
- ✅ UI blocking < 10%

### Should-Have (Success Criteria)
- ✅ Startup < 200ms
- ✅ Memory < 30MB
- ✅ FPS = 60fps sustained
- ✅ UI blocking = 0%

### Stretch Goals (Nice-to-Have)
- 🎯 Startup < 100ms
- 🎯 Memory < 25MB
- 🎯 FPS = 120fps (with render thread)
- 🎯 Tab switching < 10ms

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goals**: Set up TUIjoli + Bun, port basic layout, establish IPC
**Target**: Startup < 300ms
**Read**: Sections 1-3 of TUIJOLI-ARCHITECTURE-EXAMPLES.md

### Phase 2: Core Features (Week 3-4)
**Goals**: Port Single URL tab, implement worker thread, migrate cache/metrics
**Target**: Startup < 200ms, Memory < 35MB
**Read**: Sections 4-6 of TUIJOLI-ARCHITECTURE-EXAMPLES.md

### Phase 3: Advanced Features (Week 5-6)
**Goals**: Port Batch tab, streaming results, incremental rendering, Metrics tab
**Target**: 60fps sustained, Memory < 30MB
**Read**: Section 3 (Rendering) of TUIJOLI-PERFORMANCE-OPTIMIZATION.md

### Phase 4: Polish & Profiling (Week 7-8)
**Goals**: Performance dashboard, rendering optimizations, benchmark suite, CI tests
**Target**: All stretch goals
**Read**: Section 6 (Profiling) of TUIJOLI-PERFORMANCE-OPTIMIZATION.md

---

## Common Questions

### Q: Why migrate from Python/Textual to Bun/TUIjoli?

**A**: Performance and user experience:
- **75-85% faster startup** (Bun runtime vs Python interpreter)
- **30-50% less memory** (native Zig buffers vs Python objects)
- **100% UI responsiveness** (worker threads for scraping)
- **60fps sustained** (native rendering with incremental updates)

### Q: What about the existing Python backend?

**A**: Keep it! Use Bun ↔ Python IPC bridge:
- All scraping logic stays in Python (scraper/ modules)
- IPC overhead is negligible (<5ms per call)
- Optionally migrate hot paths (cache, metrics) to TypeScript for 2-3× speedup

### Q: Is this worth the effort?

**A**: For Scrapouille, yes:
- **User experience**: No more UI freezing during scraping (current pain point)
- **Performance**: 60-70% faster perceived performance
- **Developer experience**: Bun hot reload <100ms (vs Python's ~1s)
- **Future-proof**: TUIjoli is actively developed, Textual may not be optimal long-term

### Q: What are the risks?

**A**: Main risks and mitigations:
- **Feature parity**: Phase-by-phase migration with testing (keep Streamlit as fallback)
- **IPC overhead**: Keep calls coarse-grained (5-10s scraping operations)
- **Worker instability**: Extensive error handling + fallback to main thread
- **Memory leaks**: Arena allocators + comprehensive stress testing

### Q: How do I validate performance improvements?

**A**: Follow the checklist in PERFORMANCE-BENCHMARKS.md:
1. Run startup benchmarks (hyperfine)
2. Run memory benchmarks (bun:test)
3. Run rendering benchmarks (renderStats)
4. Test real-world use cases
5. Check CI performance regression tests

### Q: What if targets aren't met?

**A**: Decision tree:
- **<50% improvement**: Reconsider migration, investigate bottlenecks
- **50-80% improvement**: Proceed with caveats, document limitations
- **>80% improvement**: Celebrate and proceed to production

---

## Performance Measurement Tools

### Startup Time
```bash
# Baseline (Python/Textual)
hyperfine --warmup 0 --runs 10 'python tui.py --benchmark-mode'

# Target (TUIjoli)
hyperfine --warmup 0 --runs 10 'bun run src/main.ts --benchmark-mode'
```

### Memory Usage
```typescript
// In code
const memory = process.memoryUsage();
console.log((memory.heapUsed / 1024 / 1024).toFixed(2), 'MB');
```

### Rendering Performance
```typescript
// Leverage TUIjoli's built-in stats
const stats = tuijoli.getRendererStats();
console.log(`FPS: ${stats.fps}, Cells: ${stats.cellsUpdated}`);
```

### Async Operations
```typescript
// Use custom profiler
import { profiler } from './profiler';
profiler.start('scrape');
await scrapeSingle(url);
profiler.end('scrape');
profiler.report();
```

---

## Contributing

### Adding Benchmarks
1. Create benchmark file in `benchmarks/`
2. Use `mitata` library for consistent measurement
3. Add to CI workflow in `.github/workflows/performance.yml`
4. Update PERFORMANCE-BENCHMARKS.md with results

### Reporting Performance Issues
1. Run profiler to identify bottleneck
2. Check renderStats for rendering issues
3. Use memory profiler (bun --inspect) for leaks
4. Create issue with profiler output + reproduction steps

### Optimizing Performance
1. Identify bottleneck with profiler
2. Check relevant section in TUIJOLI-PERFORMANCE-OPTIMIZATION.md
3. Review code examples in TUIJOLI-ARCHITECTURE-EXAMPLES.md
4. Implement optimization
5. Validate with benchmarks
6. Update documentation if new pattern

---

## External Resources

### TUIjoli Documentation
- **GitHub**: https://github.com/BasicFist/TUIjoli
- **Core Package**: packages/core/src/zig/ (native Zig layer)
- **Renderer**: renderer.zig (60fps rendering engine)
- **Buffer**: buffer.zig (optimized cell buffers)
- **Text Buffer**: text-buffer.zig (virtualized text rendering)

### Bun Documentation
- **Runtime**: https://bun.sh/docs/runtime
- **Workers**: https://bun.sh/docs/api/workers
- **SQLite**: https://bun.sh/docs/api/sqlite
- **subprocess**: https://bun.sh/docs/api/spawn

### Performance Tools
- **hyperfine**: https://github.com/sharkdp/hyperfine (CLI benchmarking)
- **mitata**: https://github.com/evanwashere/mitata (JavaScript benchmarking)
- **Chrome DevTools**: chrome://inspect (Bun profiling)

---

## Status & Next Steps

### Current Status
- ✅ Documentation complete (3 comprehensive documents, 81KB total)
- ✅ Architecture designed (IPC bridge, worker threads, native backends)
- ✅ Performance targets defined (75-85% startup, 30-50% memory)
- ⏳ Implementation pending (Phase 1: Foundation)

### Next Steps
1. **Baseline Measurement** (1 day)
   - Run all benchmarks on current Textual TUI
   - Document baseline performance
   - Update PERFORMANCE-BENCHMARKS.md with actual numbers

2. **Phase 1: Foundation** (1-2 weeks)
   - Set up TUIjoli + Bun project structure
   - Implement basic IPC bridge
   - Port StatusBar + TabContainer
   - Validate startup time < 300ms

3. **Phase 2: Core Features** (2-3 weeks)
   - Port Single URL tab
   - Implement worker thread
   - Migrate cache + metrics to TypeScript
   - Validate memory < 35MB

4. **Phase 3+**: Continue per roadmap

---

## Contact & Support

**Questions about performance optimization?**
- Check relevant section in TUIJOLI-PERFORMANCE-OPTIMIZATION.md
- Review code examples in TUIJOLI-ARCHITECTURE-EXAMPLES.md
- Consult benchmarks in PERFORMANCE-BENCHMARKS.md

**Found a performance issue?**
- Run profiler (see "Performance Measurement Tools" above)
- Check if it's a known limitation (see "Risk Assessment" in optimization doc)
- Create issue with profiler output

**Ready to implement?**
- Start with "Quick Start Guide" above
- Follow implementation roadmap
- Reference code examples as needed

---

**Last Updated**: 2025-11-11
**Document Series Version**: 1.0
**Status**: Ready for Phase 1 implementation
