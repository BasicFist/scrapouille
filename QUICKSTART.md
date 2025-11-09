# Quick Start Guide

## ✅ What's Ready

- ✓ Project structure created at `ai/services/web-scraper/`
- ✓ Python dependencies installed in `venv/`
- ✓ Ollama is running
- ✓ LLM models available (llama3.1, qwen2.5-coder, deepseek-coder-v2)
- ⏳ Embedding model (nomic-embed-text) downloading

## 🚀 Start the Scraper

```bash
cd /home/miko/LAB/dev/ai/services/web-scraper

# Activate environment
source venv/bin/activate

# Start Streamlit app
streamlit run scraper.py
```

Opens at: **http://localhost:8501**

## 📋 Verify Setup

```bash
# Check model status
curl -s http://localhost:11434/api/tags | grep -E "(llama3.1|nomic-embed)"

# Run health check
./test.sh
```

## 🧪 Test Example

1. **URL**: `https://news.ycombinator.com`
2. **Prompt**: `Extract the top 5 post titles and their scores`
3. **Model**: Select `llama3.1`
4. **Click**: Scrape

## ⚠️ If Embedding Model Not Ready

The `nomic-embed-text` model may still be downloading (274MB). Check with:

```bash
curl -s http://localhost:11434/api/tags | grep nomic-embed-text
```

If missing, pull manually:

```bash
curl -X POST http://localhost:11434/api/pull -d '{"name":"nomic-embed-text"}'
```

## 📁 Project Structure

```
ai/services/web-scraper/
├── scraper.py          # Main Streamlit app
├── requirements.txt    # Python dependencies  
├── setup.sh           # Setup script
├── test.sh            # Health check
├── README.md          # Full documentation
├── QUICKSTART.md      # This file
└── venv/              # Virtual environment
```

## 🎯 Next Steps

1. Wait for embedding model to finish downloading
2. Run `./test.sh` to verify all components
3. Start the app with `streamlit run scraper.py`
4. Test with a simple website

## 💡 Tips

- **llama3.1**: Best for general web scraping (fastest)
- **qwen2.5-coder**: Great for technical/code content
- **deepseek-coder-v2**: For complex structured data (slower)

Need help? See `README.md` for full documentation.
