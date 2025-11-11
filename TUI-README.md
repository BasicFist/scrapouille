# Scrapouille TUI - Terminal User Interface

A beautiful, feature-rich terminal interface for Scrapouille, inspired by [TUIjoli](https://github.com/BasicFist/TUIjoli) architecture.

## Features

- **🎯 Interactive Interface**: Beautiful terminal UI with tabbed navigation
- **📊 Real-time Metrics**: Live execution stats and performance monitoring
- **🚀 Batch Processing**: Process multiple URLs concurrently with progress tracking
- **💾 Smart Caching**: Redis-powered caching with hit rate monitoring
- **🔄 Model Fallback**: Automatic failover across multiple LLM models
- **🛡️ Stealth Mode**: Anti-detection features to prevent IP bans
- **📈 Analytics Dashboard**: View 7-day statistics and model usage
- **⚡ Rate Limiting**: Ethical scraping with configurable delays
- **✅ Schema Validation**: Pydantic-powered data validation

## Installation

The TUI requires additional dependencies beyond the standard Scrapouille installation:

```bash
# Already in requirements.txt
pip install textual>=0.47.0 httpx>=0.25.0
```

## Quick Start

```bash
# Launch TUI with automatic environment checks
./run-tui.sh

# Or manually
source venv-isolated/bin/activate
python tui.py
```

## Interface Overview

### Single URL Tab

Scrape individual URLs with full control over:
- **Template System**: Choose from 7 pre-built templates or write custom prompts
- **Model Selection**: Primary model with automatic fallback chain
- **Rate Limiting**: 4 presets (None, Aggressive, Normal, Polite)
- **Stealth Mode**: 4 levels (Off, Low, Medium, High)
- **Validation**: Optional Pydantic schema validation
- **Results Display**: JSON-formatted output with syntax highlighting
- **Metrics Panel**: Real-time execution stats

**Workflow:**
1. Enter URL to scrape
2. Select template or write custom prompt
3. Configure model, rate limiting, and stealth settings
4. Click "Scrape" button
5. View results and metrics in real-time

### Batch Processing Tab

Process multiple URLs concurrently:
- **URL Input**: Paste multiple URLs (one per line)
- **Shared Prompt**: Single prompt applied to all URLs
- **Concurrency Control**: 1-20 concurrent requests
- **Timeout Configuration**: 30-120 seconds per URL
- **Progress Tracking**: Real-time progress bar and status updates
- **Results Table**: Detailed status for each URL
- **Summary Stats**: Success rate, cache hits, timing

**Workflow:**
1. Enter URLs (one per line) in textarea
2. Write shared prompt for all URLs
3. Configure concurrency, timeout, and options
4. Click "Start Batch" to begin processing
5. Monitor real-time progress
6. View detailed results in table
7. Export to CSV/JSON (coming soon)

### Metrics Dashboard Tab

View analytics and performance data:
- **7-Day Statistics**: Total scrapes, average time, cache hit rate, error rate
- **Model Usage**: Distribution of model usage across scrapes
- **Recent Scrapes**: Table of last 20 scrape operations
- **Refresh Button**: Update metrics on demand

### Configuration Tab

Manage application settings:
- **Ollama Settings**: Base URL for Ollama server
- **Redis Settings**: Host and port for Redis cache
- **Default Behaviors**: Rate limiting and stealth mode defaults
- **Save Configuration**: Persist settings (coming soon)

### Help Tab

Quick reference guide:
- Keyboard shortcuts
- Feature descriptions
- Rate limiting modes explanation
- Stealth levels explanation
- Version information

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Q` | Quit application |
| `Ctrl+T` | Switch tabs |
| `Tab` | Navigate between fields |
| `Enter` | Activate focused button |
| `Ctrl+C` | Copy selected text |

## Architecture

### Technology Stack

- **Framework**: [Textual](https://textual.textualize.io/) - Modern Python TUI framework
- **Backend**: Scrapouille scraper modules (fallback, cache, metrics, stealth)
- **Database**: SQLite (metrics), Redis (caching)
- **LLM**: Ollama (local models)

### Component Architecture

```
tui.py (Main Application)
├── StatusBar          - Connection status indicators
├── TabbedContent      - Tab navigation
│   ├── SingleURLTab   - Single URL scraping interface
│   ├── BatchTab       - Batch processing interface
│   ├── MetricsTab     - Analytics dashboard
│   ├── ConfigTab      - Configuration screen
│   └── HelpTab        - Documentation
└── Footer             - Keyboard shortcuts

scraper/tui_integration.py (Backend Bridge)
├── TUIScraperBackend
│   ├── scrape_single_url()    - Single URL scraping
│   ├── scrape_batch()          - Batch processing
│   ├── get_metrics_stats()     - Analytics data
│   └── check_ollama_connection() - Health checks
```

### Design Philosophy

Inspired by **TUIjoli**'s architecture:
- **Component-based**: Modular, reusable UI components
- **Reactive UI**: Real-time updates with Textual's reactive properties
- **Async-first**: All I/O operations are asynchronous
- **Type-safe**: Full type hints throughout codebase
- **Testable**: Backend logic separated from UI layer

## Integration with Scrapouille Backend

The TUI uses `scraper/tui_integration.py` to bridge the UI and backend:

### Single URL Scraping

```python
result, metadata = await backend.scrape_single_url(
    url="https://example.com",
    prompt="Extract main content",
    model="qwen2.5-coder:7b",
    schema_name="article",
    rate_limit_mode="normal",
    stealth_level="medium",
    use_cache=True,
    markdown_mode=False,
)
# metadata includes: execution_time, model_used, fallback_attempts, cached, validation_passed
```

### Batch Processing

```python
results = await backend.scrape_batch(
    urls=["url1", "url2", "url3"],
    prompt="Extract products",
    max_concurrent=5,
    timeout_per_url=30.0,
    use_cache=True,
    use_rate_limiting=True,
    use_stealth=True,
    progress_callback=lambda done, total, url: print(f"{done}/{total}"),
)
# Returns list of BatchResult objects
```

## Status Indicators

### Ollama Connection
- 🟢 Connected - Ollama server is running and accessible
- 🔴 Disconnected - Ollama not detected (scraping will fail)

### Redis Connection
- 🟢 Connected - Redis is running (caching enabled)
- ⚪ Disconnected - Redis not detected (caching disabled, degraded gracefully)

## Performance

- **Startup**: <1 second (fast initialization)
- **Rendering**: 60fps terminal rendering (powered by Textual)
- **Responsiveness**: Non-blocking async operations
- **Memory**: ~50MB RAM for UI + backend overhead

## Comparison: TUI vs Streamlit

| Feature | TUI | Streamlit UI |
|---------|-----|--------------|
| **Startup Time** | <1s | 3-5s |
| **Memory Usage** | ~50MB | ~200MB |
| **Remote Access** | SSH-friendly | Requires port forwarding |
| **Keyboard Nav** | Full support | Limited |
| **Batch Progress** | Real-time | Page refresh required |
| **Aesthetics** | Terminal-native | Web-based |
| **Use Case** | Dev/Server | Demo/Production |

**When to use TUI:**
- SSH/remote server environments
- Low-latency local development
- Keyboard-first workflows
- Minimal resource overhead
- Terminal-native workflows

**When to use Streamlit:**
- Web browser preference
- Sharing with non-technical users
- Richer visualizations
- File upload/download features

## Troubleshooting

### TUI won't start

```bash
# Check if dependencies are installed
pip list | grep textual

# Reinstall if needed
pip install -r requirements.txt
```

### Ollama connection failed

```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull qwen2.5-coder:7b

# Test connection
curl http://localhost:11434/api/tags
```

### Redis caching not working

```bash
# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return "PONG"

# TUI will gracefully degrade if Redis unavailable
```

### Textual rendering issues

```bash
# Ensure terminal supports ANSI codes
echo $TERM  # Should be xterm-256color or similar

# Use a modern terminal:
# - Linux: kitty, alacritty, GNOME Terminal
# - macOS: iTerm2, Terminal.app
# - Windows: Windows Terminal
```

### Performance issues

```bash
# Reduce concurrency in batch processing
# Use lower stealth levels
# Disable caching if Redis is slow
# Check Ollama model performance
```

## Development

### File Structure

```
scrapouille/
├── tui.py                      # Main TUI application
├── run-tui.sh                  # Launcher script
├── scraper/
│   └── tui_integration.py      # Backend bridge
└── TUI-README.md              # This file
```

### Adding New Features

1. **New Tab**: Add `TabPane` in `ScrapouilleApp.compose()`
2. **New Widget**: Create component class extending `Widget`
3. **Backend Method**: Add to `TUIScraperBackend` class
4. **Styling**: Update CSS in `ScrapouilleApp.CSS`

### Testing

```bash
# Run TUI in development mode
python tui.py

# Test backend integration
pytest tests/test_tui_integration.py  # (TODO: create tests)

# Test UI components
# (Textual supports snapshot testing)
```

## Roadmap

- [ ] **Export Features**: CSV/JSON export for batch results
- [ ] **Configuration Persistence**: Save settings to file
- [ ] **Advanced Filtering**: Filter metrics by date range, model, status
- [ ] **Live Log Viewer**: Stream scraping logs in real-time
- [ ] **Keyboard Macros**: Record and replay common workflows
- [ ] **Theme Support**: Light/dark themes and custom color schemes
- [ ] **Split View**: View multiple tabs side-by-side
- [ ] **Search/Filter**: Search through results and metrics
- [ ] **Graph Visualization**: Charts for metrics (via plotext)
- [ ] **Session Management**: Save and resume scraping sessions

## Credits

- **Scrapouille**: AI-powered web scraping engine
- **Textual**: Modern Python TUI framework by [Textualize.io](https://www.textualize.io/)
- **TUIjoli**: Terminal UI library inspiration
- **Claude Code**: TUI architecture design and implementation

## License

MIT License - Same as Scrapouille

## Version

**v3.0 Phase 4** - November 2025

Features: Single URL scraping, Batch processing, Metrics dashboard, Model fallback, Rate limiting, Stealth mode, Redis caching, Schema validation
