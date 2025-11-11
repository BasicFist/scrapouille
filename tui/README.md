# Scrapouille TUI (TUIjoli)

TypeScript Terminal UI for Scrapouille, built with TUIjoli and SolidJS.

## Prerequisites

- **Bun** >= 1.2.0 ([Install](https://bun.sh))
- **Zig** >= 0.14.1 ([Install](https://ziglang.org/download/)) - Required for TUIjoli native bindings
- **TUIjoli** - Development version linked from `/home/miko/LAB/dev/TUIjoli`

## Setup

```bash
# 1. Install Bun dependencies
bun install

# 2. Link TUIjoli development version (includes SolidJS reconciler)
bun run link-tuijoli
# Or manually:
# cd /home/miko/LAB/dev/TUIjoli
# ./scripts/link-tuijoli-dev.sh /home/miko/LAB/ai/services/scrapouille/tui --solid

# 3. Verify TUIjoli is linked
ls -la node_modules/@tuijoli
```

## Development

```bash
# Start TUI (requires API server running on :8000)
bun run dev

# Type check
bun run typecheck

# Run tests
bun test
```

## Project Structure

```
tui/
├── src/
│   ├── main.ts              # Entry point
│   ├── api/
│   │   ├── client.ts        # HTTP client for backend API
│   │   └── types.ts         # TypeScript types for API
│   ├── components/
│   │   ├── App.tsx          # Main application component
│   │   ├── StatusBar.tsx    # Status bar with connection indicators
│   │   └── ...              # Other components
│   ├── stores/
│   │   └── app.ts           # Global state management (SolidJS signals)
│   └── utils/
│       └── logger.ts        # Logging utilities
├── package.json
├── tsconfig.json
└── README.md
```

## Phase 1 Goals

- [x] Project setup with Bun + TypeScript
- [x] TUIjoli + SolidJS integration
- [ ] Basic app shell with "Hello World"
- [ ] HTTP client for backend API
- [ ] Health check integration
- [ ] Tab navigation placeholder

## Architecture

```
TypeScript TUI (Bun) ──HTTP/JSON──> FastAPI Server (Python) ──> Scraper Modules
```

The TUI communicates with the Python backend via REST API running on `localhost:8000`.

## Performance Targets

- **Startup time**: <1 second
- **Memory usage**: ~50MB
- **Frame rate**: 60fps sustained
- **API latency**: <5ms (localhost)
