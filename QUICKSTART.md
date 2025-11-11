# Scrapouille Quick Start Guide

**Version:** v3.0 Phase 4 (November 2025)

## 🚀 Choose Your Interface

Scrapouille offers two interfaces - pick what works best for you:

### Option A: Terminal UI (TUI) - Recommended for Dev/SSH ⚡

Fast, lightweight, keyboard-driven interface inspired by TUIjoli.

```bash
# Quick launch
./run-tui.sh

# Or manually
source venv-isolated/bin/activate
python tui.py
```

**Features:**
- <1s startup time
- SSH/remote-friendly
- Keyboard navigation (Ctrl+Q to quit, Ctrl+T for tabs)
- ~50MB memory footprint
- All scraping features available

### Option B: Streamlit Web UI - Original Interface 🌐

Browser-based interface with rich visualizations.

```bash
source venv-isolated/bin/activate
streamlit run scraper.py
```

Opens at **http://localhost:8501**

---

## ✅ Prerequisites

Before starting, ensure you have:

### 1. Virtual Environment

```bash
# Must use venv-isolated (NOT venv)
source venv-isolated/bin/activate
```

### 2. Ollama Running

```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags

# Pull recommended model
ollama pull qwen2.5-coder:7b
```

### 3. Redis (Optional, for caching)

```bash
# Start Redis
redis-server

# Verify connection
redis-cli ping  # Should return "PONG"
```

**Note:** If Redis isn't available, caching gracefully degrades.

---

## 🧪 Quick Test

### Using TUI:

1. Launch: `./run-tui.sh`
2. Enter URL: `https://news.ycombinator.com`
3. Select template: **"News Articles"**
4. Click **"Scrape"**
5. View results in JSON panel

### Using Web UI:

1. Launch: `streamlit run scraper.py`
2. Navigate to http://localhost:8501
3. Enter URL: `https://example.com/product`
4. Select template: **"E-commerce Products"**
5. Optional: Choose schema **"Product"**
6. Click **"Scrape!"**

---

## 📁 Project Structure

```
scrapouille/
├── tui.py                    # Terminal UI (v3.0 Phase 4)
├── scraper.py                # Streamlit Web UI
├── run-tui.sh                # TUI launcher
├── .scrapouille_aliases      # Shell aliases
├── scraper/                  # Backend modules
│   ├── fallback.py           # Model fallback chain
│   ├── cache.py              # Redis caching
│   ├── metrics.py            # SQLite metrics
│   ├── batch.py              # Async batch processing
│   ├── stealth.py            # Anti-detection
│   ├── ratelimit.py          # Rate limiting
│   ├── models.py             # Validation schemas
│   ├── templates.py          # Few-shot prompts
│   └── tui_integration.py    # TUI backend bridge
├── data/
│   └── metrics.db            # Metrics database
├── requirements.txt          # Dependencies
├── venv-isolated/            # Virtual environment
├── README.md                 # Full documentation
├── TUI-README.md             # TUI documentation
├── QUICKSTART.md             # This file
└── CLAUDE.md                 # Developer guide
```

---

## ⚡ Shell Aliases (Optional)

Set up quick commands:

```bash
# Source aliases
source .scrapouille_aliases

# Or add permanently to ~/.bashrc or ~/.zshrc:
echo "source $(pwd)/.scrapouille_aliases" >> ~/.bashrc
source ~/.bashrc
```

**Available aliases:**
- `stui` - Launch Terminal UI
- `sweb` - Launch Web UI
- `scrapouille` - Default to TUI
- `scrapouille-test` - Run tests
- `scrapouille-help` - Show TUI docs

---

## 🎯 Features Overview

### v3.0 Phase 4 Features:

✅ **Dual Interfaces**: Terminal UI + Web UI
✅ **Model Fallback**: Automatic failover (99.9% uptime)
✅ **Redis Caching**: 80-95% speed improvement
✅ **Batch Processing**: 10-100 URLs concurrently
✅ **Rate Limiting**: 4 presets for ethical scraping
✅ **Stealth Mode**: 4 levels of anti-detection
✅ **Schema Validation**: 5 pre-built Pydantic schemas
✅ **Metrics Dashboard**: 7-day analytics
✅ **Template System**: 7 few-shot prompt templates

---

## 💡 Model Recommendations

| Model | Best For | Speed | Accuracy |
|-------|----------|-------|----------|
| **qwen2.5-coder:7b** | General scraping | Fast | High |
| **llama3.1** | News, articles | Very Fast | Good |
| **deepseek-coder-v2** | Complex data | Slow | Very High |

---

## 🔧 Troubleshooting

### TUI won't start

```bash
# Check dependencies
pip list | grep textual

# Reinstall if needed
pip install -r requirements.txt
```

### Ollama connection refused

```bash
# Start Ollama
ollama serve

# Check models
ollama list
```

### Redis not working

```bash
# Start Redis
redis-server

# Test connection
redis-cli ping
```

**Note:** TUI shows connection status in the status bar:
- 🟢 = Connected
- 🔴 = Disconnected (Ollama)
- ⚪ = Disconnected (Redis, graceful degradation)

---

## 📚 Next Steps

1. ✅ Choose your interface (TUI or Web UI)
2. ✅ Run a test scrape
3. 📖 Read full docs:
   - [README.md](README.md) - Complete feature documentation
   - [TUI-README.md](TUI-README.md) - Terminal UI guide
   - [CLAUDE.md](CLAUDE.md) - Developer reference
4. 🎨 Explore features:
   - Try batch processing (multiple URLs)
   - Enable stealth mode
   - View metrics dashboard
   - Test different templates

---

## 🆘 Need Help?

- **TUI Help Tab**: Press Ctrl+T and select "Help" tab
- **Documentation**: `cat TUI-README.md` or `cat README.md`
- **Test Suite**: `python test_integration_quick.py`
- **GitHub Issues**: [Report bugs](https://github.com/BasicFist/scrapouille/issues)

---

**Happy Scraping! 🕷️**
