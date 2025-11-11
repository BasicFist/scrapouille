# Textual to TUIjoli Migration Guide

**Version**: Scrapouille v3.0 Phase 4
**Target Framework**: TUIjoli (OpenTUI) with React or SolidJS reconciler
**Date**: 2025-11-11

---

## Executive Summary

This guide provides a practical, step-by-step migration strategy from Textual's Python class-based widget system to TUIjoli's TypeScript functional component architecture. The migration preserves all functionality while modernizing the codebase with React/Solid patterns.

**Key Benefits of Migration**:
- **10-100x faster startup**: <100ms vs 3-5s (Textual/Streamlit)
- **4x lower memory**: ~15MB vs ~50MB (Textual)
- **Modern patterns**: Functional components vs class-based widgets
- **Better testability**: Pure functions vs stateful classes
- **Rich ecosystem**: NPM packages, TypeScript tooling
- **Cross-platform**: Identical experience on all platforms

---

## 1. Component Mapping Table

| Textual Component | TUIjoli Equivalent | Migration Notes |
|-------------------|-------------------|-----------------|
| `App` | `createCliRenderer()` + `createRoot()` | Main app becomes renderer + root component |
| `Static` | `<text>` | Simple text display with styling |
| `Label` | `<text>` | Use `content` prop instead of markup |
| `Input` | `<input>` | Similar API, use `onInput` instead of `on` handler |
| `TextArea` | `<textarea>` | Multi-line input, access with ref |
| `Button` | `<box>` + `onMouse` | Create custom button component |
| `Select` | `<select>` | Options array, `onChange` callback |
| `Checkbox` | Custom component | Build from `<box>` + `<text>` + state |
| `DataTable` | Custom component | Build from `<scrollbox>` + grid layout |
| `ProgressBar` | Custom component | Use `<box>` with dynamic width |
| `Log` | `<scrollbox>` + `<text>` | Scrollable text container |
| `Container` / `Horizontal` / `VerticalScroll` | `<box>` | Use `flexDirection`, `overflow` props |
| `TabbedContent` / `TabPane` | Custom tab system | Build from `<box>` + state + `<select>` or buttons |
| `Header` / `Footer` | `<box>` | Fixed position boxes |
| `reactive` properties | React `useState()` / Solid `createSignal()` | Reactive state management |
| CSS styling | Inline `style` prop | Convert CSS rules to JS objects |
| `on_mount` | React `useEffect(() => {}, [])` / Solid `onMount()` | Lifecycle hooks |
| `on_*` event handlers | `onMouse`, `onInput`, etc. | Event props on components |
| `query_one()` | React `useRef()` / Solid refs | Direct DOM-like access |

---

## 2. Migration Patterns

### 2.1 State Management

**Textual (Python):**
```python
class StatusBar(Static):
    status_text = reactive("Ready")
    ollama_connected = reactive(False)
    redis_connected = reactive(False)

    def render(self) -> str:
        ollama_icon = "🟢" if self.ollama_connected else "🔴"
        return f"Status: {self.status_text} | Ollama {ollama_icon}"
```

**TUIjoli React (TypeScript):**
```tsx
function StatusBar() {
  const [statusText, setStatusText] = useState("Ready")
  const [ollamaConnected, setOllamaConnected] = useState(false)
  const [redisConnected, setRedisConnected] = useState(false)

  const ollamaIcon = ollamaConnected ? "🟢" : "🔴"
  const redisIcon = redisConnected ? "🟢" : "⚪"

  return (
    <box style={{ position: "absolute", bottom: 0, width: "100%", height: 1, backgroundColor: "#1e40af" }}>
      <text content={`Status: ${statusText} | Ollama ${ollamaIcon} | Redis ${redisIcon}`} />
    </box>
  )
}
```

**TUIjoli Solid (TypeScript):**
```tsx
function StatusBar() {
  const [statusText, setStatusText] = createSignal("Ready")
  const [ollamaConnected, setOllamaConnected] = createSignal(false)
  const [redisConnected, setRedisConnected] = createSignal(false)

  const ollamaIcon = () => ollamaConnected() ? "🟢" : "🔴"
  const redisIcon = () => redisConnected() ? "🟢" : "⚪"

  return (
    <box style={{ position: "absolute", bottom: 0, width: "100%", height: 1, backgroundColor: "#1e40af" }}>
      <text content={`Status: ${statusText()} | Ollama ${ollamaIcon()} | Redis ${redisIcon()}`} />
    </box>
  )
}
```

**Key Differences**:
- Textual: `reactive` class attributes, auto-rendering on change
- React: `useState` hooks, re-render on state change
- Solid: `createSignal` with getter/setter, fine-grained reactivity

---

### 2.2 Event Handling

**Textual (Python):**
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id
    if button_id == "scrape_button":
        self.scrape_single_url()

def scrape_single_url(self) -> None:
    asyncio.create_task(self._scrape_single_url_async())
```

**TUIjoli React (TypeScript):**
```tsx
function SingleURLTab() {
  const handleScrapeClick = useCallback(async () => {
    await scrapeSingleURL()
  }, [])

  return (
    <box>
      <CustomButton
        label="Scrape"
        onClick={handleScrapeClick}
        variant="primary"
      />
    </box>
  )
}

// Custom Button Component
function CustomButton({ label, onClick, variant = "default" }: ButtonProps) {
  const [isPressed, setIsPressed] = useState(false)

  const bgColor = variant === "primary" ? "#3b82f6" : "#6b7280"
  const hoverColor = variant === "primary" ? "#2563eb" : "#4b5563"

  return (
    <box
      style={{
        backgroundColor: isPressed ? hoverColor : bgColor,
        border: true,
        borderStyle: "rounded",
        padding: { top: 0, bottom: 0, left: 1, right: 1 },
        height: 3,
      }}
      onMouse={(event) => {
        if (event.type === "down") {
          setIsPressed(true)
          onClick?.()
        } else if (event.type === "up") {
          setIsPressed(false)
        }
      }}
    >
      <text content={label} fg="#ffffff" />
    </box>
  )
}
```

**TUIjoli Solid (TypeScript):**
```tsx
function SingleURLTab() {
  const handleScrapeClick = async () => {
    await scrapeSingleURL()
  }

  return (
    <box>
      <CustomButton
        label="Scrape"
        onClick={handleScrapeClick}
        variant="primary"
      />
    </box>
  )
}

function CustomButton(props: ButtonProps) {
  const [isPressed, setIsPressed] = createSignal(false)

  const bgColor = () => props.variant === "primary" ? "#3b82f6" : "#6b7280"
  const hoverColor = () => props.variant === "primary" ? "#2563eb" : "#4b5563"

  return (
    <box
      style={{
        backgroundColor: isPressed() ? hoverColor() : bgColor(),
        border: true,
        borderStyle: "rounded",
        padding: { top: 0, bottom: 0, left: 1, right: 1 },
        height: 3,
      }}
      onMouse={(event) => {
        if (event.type === "down") {
          setIsPressed(true)
          props.onClick?.()
        } else if (event.type === "up") {
          setIsPressed(false)
        }
      }}
    >
      <text content={props.label} fg="#ffffff" />
    </box>
  )
}
```

**Key Differences**:
- Textual: `on_*` methods, event types in method signature
- TUIjoli: `onMouse`, `onInput` props, event object parameter
- React: `useCallback` for stable function references
- Solid: Direct function definitions, auto-memoization

---

### 2.3 Lifecycle Hooks

**Textual (Python):**
```python
async def on_mount(self) -> None:
    # Initialize cache
    self.cache = ScraperCache(enabled=True, default_ttl_hours=24)

    # Check Ollama connection
    await self.check_ollama_connection()

    # Initialize tables
    table = self.query_one("#batch_results_table", DataTable)
    table.add_columns("URL", "Status", "Time", "Model")
```

**TUIjoli React (TypeScript):**
```tsx
function App() {
  const [cache, setCache] = useState<ScraperCache | null>(null)
  const [ollamaConnected, setOllamaConnected] = useState(false)
  const renderer = useRenderer()

  // Mount effect (runs once)
  useEffect(() => {
    const initializeApp = async () => {
      // Initialize cache
      const cacheInstance = new ScraperCache({ enabled: true, defaultTTLHours: 24 })
      setCache(cacheInstance)

      // Check Ollama connection
      const connected = await checkOllamaConnection()
      setOllamaConnected(connected)
    }

    initializeApp()
  }, []) // Empty deps = mount only

  // Cleanup effect
  useEffect(() => {
    return () => {
      cache?.close()
    }
  }, [cache])

  return (
    <box>
      <BatchResultsTable />
    </box>
  )
}
```

**TUIjoli Solid (TypeScript):**
```tsx
function App() {
  const [cache, setCache] = createSignal<ScraperCache | null>(null)
  const [ollamaConnected, setOllamaConnected] = createSignal(false)
  const renderer = useRenderer()

  // Mount effect (runs once)
  onMount(async () => {
    // Initialize cache
    const cacheInstance = new ScraperCache({ enabled: true, defaultTTLHours: 24 })
    setCache(cacheInstance)

    // Check Ollama connection
    const connected = await checkOllamaConnection()
    setOllamaConnected(connected)
  })

  // Cleanup effect
  onCleanup(() => {
    cache()?.close()
  })

  return (
    <box>
      <BatchResultsTable />
    </box>
  )
}
```

**Key Differences**:
- Textual: `on_mount()` async method, auto-called by framework
- React: `useEffect(() => {}, [])` for mount, return cleanup function
- Solid: `onMount()` for mount, `onCleanup()` for cleanup
- Both TUIjoli: Explicit async/await, Promise handling

---

### 2.4 Async Operations

**Textual (Python):**
```python
def scrape_single_url(self) -> None:
    asyncio.create_task(self._scrape_single_url_async())

async def _scrape_single_url_async(self) -> None:
    url_input = self.query_one("#url_input", Input)
    url = url_input.value.strip()

    # Update status
    status_bar = self.query_one("#status_bar", StatusBar)
    status_bar.status_text = "Scraping..."

    try:
        result, metadata = await self.backend.scrape_single_url(url=url, prompt=prompt)
        # Display results...
    except Exception as e:
        self.notify(f"Error: {str(e)}", severity="error")
```

**TUIjoli React (TypeScript):**
```tsx
function SingleURLTab() {
  const [url, setUrl] = useState("")
  const [status, setStatus] = useState("Ready")
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleScrape = useCallback(async () => {
    if (!url.trim()) {
      alert("Please enter a URL")
      return
    }

    setLoading(true)
    setStatus("Scraping...")

    try {
      const { result, metadata } = await backend.scrapeSingleURL({ url, prompt })
      setResult(result)
      setStatus("Completed")
    } catch (error) {
      setStatus(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }, [url])

  return (
    <box>
      <input
        placeholder="https://example.com"
        onInput={setUrl}
        disabled={loading}
      />
      <CustomButton
        label={loading ? "Scraping..." : "Scrape"}
        onClick={handleScrape}
        disabled={loading}
      />
      <text content={`Status: ${status}`} />
      {result && <ResultsDisplay data={result} />}
    </box>
  )
}
```

**TUIjoli Solid (TypeScript):**
```tsx
function SingleURLTab() {
  const [url, setUrl] = createSignal("")
  const [status, setStatus] = createSignal("Ready")
  const [loading, setLoading] = createSignal(false)

  // Solid's createResource for async data fetching
  const [result] = createResource(
    () => ({ url: url(), prompt: prompt() }),
    async ({ url, prompt }) => {
      if (!url.trim()) return null

      setLoading(true)
      setStatus("Scraping...")

      try {
        const { result, metadata } = await backend.scrapeSingleURL({ url, prompt })
        setStatus("Completed")
        return result
      } catch (error) {
        setStatus(`Error: ${error.message}`)
        return null
      } finally {
        setLoading(false)
      }
    }
  )

  return (
    <box>
      <input
        placeholder="https://example.com"
        onInput={(value) => setUrl(value)}
        disabled={loading()}
      />
      <CustomButton
        label={loading() ? "Scraping..." : "Scrape"}
        onClick={() => setUrl(url())} // Trigger refetch
        disabled={loading()}
      />
      <text content={`Status: ${status()}`} />
      <Show when={result()}>
        <ResultsDisplay data={result()!} />
      </Show>
    </box>
  )
}
```

**Key Differences**:
- Textual: `asyncio.create_task()`, implicit event loop
- React: `async/await` in callbacks, manual loading states
- Solid: `createResource` for declarative async data fetching
- TUIjoli: Standard Promise-based async/await

---

### 2.5 Parent-Child Communication

**Textual (Python):**
```python
# Parent updates child directly via query
class ScrapouilleApp(App):
    def update_metrics(self, metadata: dict):
        metrics_panel = self.query_one("#metrics_panel", MetricsPanel)
        metrics_panel.execution_time = metadata['execution_time']
        metrics_panel.model_used = metadata['model_used']
```

**TUIjoli React (TypeScript):**
```tsx
// Props-based communication (preferred)
function App() {
  const [metadata, setMetadata] = useState<Metadata | null>(null)

  const handleScrapeComplete = (result: any, meta: Metadata) => {
    setMetadata(meta)
  }

  return (
    <box>
      <SingleURLTab onComplete={handleScrapeComplete} />
      <MetricsPanel metadata={metadata} />
    </box>
  )
}

function MetricsPanel({ metadata }: { metadata: Metadata | null }) {
  if (!metadata) return <text content="No data yet" />

  return (
    <box>
      <text content={`Time: ${metadata.executionTime.toFixed(2)}s`} />
      <text content={`Model: ${metadata.modelUsed}`} />
    </box>
  )
}

// Or: Context-based communication (for deep trees)
const AppContext = createContext<AppContextType | null>(null)

function App() {
  const [metadata, setMetadata] = useState<Metadata | null>(null)

  return (
    <AppContext.Provider value={{ metadata, setMetadata }}>
      <SingleURLTab />
      <MetricsPanel />
    </AppContext.Provider>
  )
}

function MetricsPanel() {
  const { metadata } = useContext(AppContext)!
  // Use metadata...
}
```

**TUIjoli Solid (TypeScript):**
```tsx
// Props-based communication
function App() {
  const [metadata, setMetadata] = createSignal<Metadata | null>(null)

  const handleScrapeComplete = (result: any, meta: Metadata) => {
    setMetadata(meta)
  }

  return (
    <box>
      <SingleURLTab onComplete={handleScrapeComplete} />
      <MetricsPanel metadata={metadata()} />
    </box>
  )
}

// Or: Context-based communication
const AppContext = createContext<AppContextType>()

function App() {
  const [metadata, setMetadata] = createSignal<Metadata | null>(null)

  return (
    <AppContext.Provider value={{ metadata, setMetadata }}>
      <SingleURLTab />
      <MetricsPanel />
    </AppContext.Provider>
  )
}

function MetricsPanel() {
  const { metadata } = useContext(AppContext)!
  return (
    <Show when={metadata()}>
      <text content={`Time: ${metadata()!.executionTime.toFixed(2)}s`} />
    </Show>
  )
}
```

**Key Differences**:
- Textual: Direct child manipulation via `query_one()`
- React/Solid: Props-based or Context-based communication
- TUIjoli: Unidirectional data flow (parent → child)

---

## 3. Side-by-Side Examples

### Example 1: SingleURLTab Component

**Textual (Python) - 142 lines:**
```python
class SingleURLTab(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Single URL Scraping[/bold cyan]")
        yield Label("URL:")
        yield Input(placeholder="https://example.com", id="url_input")
        yield Label("Template (or use Custom Prompt below):")
        yield Select(
            options=[(name, name) for name in ["Custom"] + list(TEMPLATES.keys())],
            value="Custom",
            id="template_select",
        )
        # ... 130+ more lines
```

**TUIjoli React (TypeScript) - ~200 lines (estimated):**
```tsx
function SingleURLTab({ onComplete }: { onComplete: (result: any, meta: Metadata) => void }) {
  const [url, setUrl] = useState("")
  const [template, setTemplate] = useState("Custom")
  const [customPrompt, setCustomPrompt] = useState("")
  const [schema, setSchema] = useState<string | null>(null)
  const [model, setModel] = useState("qwen2.5-coder:7b")
  const [rateLimit, setRateLimit] = useState("normal")
  const [stealthLevel, setStealthLevel] = useState("off")
  const [useCache, setUseCache] = useState(true)
  const [markdownMode, setMarkdownMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const backend = useBackend()

  const handleScrape = useCallback(async () => {
    if (!url.trim()) {
      alert("Please enter a URL")
      return
    }

    const prompt = template !== "Custom" ? TEMPLATES[template] : customPrompt.trim()
    if (!prompt) {
      alert("Please enter a prompt or select a template")
      return
    }

    setLoading(true)
    try {
      const { result, metadata } = await backend.scrapeSingleURL({
        url,
        prompt,
        model,
        schemaName: schema,
        rateLimitMode: rateLimit,
        stealthLevel,
        useCache,
        markdownMode,
      })

      setResult(result)
      onComplete(result, metadata)
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }, [url, template, customPrompt, schema, model, rateLimit, stealthLevel, useCache, markdownMode])

  const handleClear = () => {
    setResult(null)
    onComplete(null, null)
  }

  return (
    <box style={{ flexDirection: "column", gap: 1, padding: 1, overflow: "scroll" }}>
      {/* Title */}
      <text content="Single URL Scraping" fg="#00FFFF" attributes={TextAttributes.BOLD} />

      {/* URL Input */}
      <text content="URL:" />
      <input
        placeholder="https://example.com"
        value={url}
        onInput={setUrl}
        disabled={loading}
        style={{ width: "100%", height: 3 }}
      />

      {/* Template Selection */}
      <text content="Template (or use Custom Prompt below):" />
      <select
        options={[
          { name: "Custom", value: "Custom" },
          ...Object.keys(TEMPLATES).map(name => ({ name, value: name }))
        ]}
        value={template}
        onChange={(_, option) => setTemplate(option.value)}
        disabled={loading}
      />

      {/* Custom Prompt */}
      <text content="Custom Prompt:" />
      <textarea
        placeholder="Enter custom prompt..."
        value={customPrompt}
        onInput={setCustomPrompt}
        disabled={loading || template !== "Custom"}
        style={{ height: 5 }}
      />

      {/* Schema Selection */}
      <text content="Validation Schema (optional):" />
      <select
        options={[
          { name: "None", value: null },
          ...Object.keys(SCHEMAS).map(name => ({ name, value: name }))
        ]}
        value={schema}
        onChange={(_, option) => setSchema(option.value)}
        disabled={loading}
      />

      {/* Model Selection */}
      <text content="Primary Model:" />
      <select
        options={[
          { name: "qwen2.5-coder:7b", value: "qwen2.5-coder:7b" },
          { name: "llama3.1", value: "llama3.1" },
          { name: "deepseek-coder-v2", value: "deepseek-coder-v2" },
        ]}
        value={model}
        onChange={(_, option) => setModel(option.value)}
        disabled={loading}
      />

      {/* Options Row */}
      <box style={{ flexDirection: "row", gap: 2 }}>
        <box style={{ flexDirection: "column" }}>
          <text content="Rate Limit:" />
          <select
            options={[
              { name: "None", value: "none" },
              { name: "Aggressive (1s)", value: "aggressive" },
              { name: "Normal (2s)", value: "normal" },
              { name: "Polite (5s)", value: "polite" },
            ]}
            value={rateLimit}
            onChange={(_, option) => setRateLimit(option.value)}
            disabled={loading}
          />
        </box>

        <box style={{ flexDirection: "column" }}>
          <text content="Stealth Mode:" />
          <select
            options={[
              { name: "Off", value: "off" },
              { name: "Low", value: "low" },
              { name: "Medium", value: "medium" },
              { name: "High", value: "high" },
            ]}
            value={stealthLevel}
            onChange={(_, option) => setStealthLevel(option.value)}
            disabled={loading}
          />
        </box>
      </box>

      {/* Checkboxes */}
      <box style={{ flexDirection: "row", gap: 2 }}>
        <Checkbox label="Use Cache" checked={useCache} onChange={setUseCache} disabled={loading} />
        <Checkbox label="Markdown Mode" checked={markdownMode} onChange={setMarkdownMode} disabled={loading} />
      </box>

      {/* Buttons */}
      <box style={{ flexDirection: "row", gap: 1 }}>
        <CustomButton label={loading ? "Scraping..." : "Scrape"} onClick={handleScrape} disabled={loading} variant="primary" />
        <CustomButton label="Clear" onClick={handleClear} disabled={loading} variant="default" />
      </box>

      {/* Results Display */}
      {result && (
        <box style={{ border: true, padding: 1, flexGrow: 1, overflow: "scroll" }}>
          <text content={JSON.stringify(result, null, 2)} fg="#00FF00" />
        </box>
      )}
    </box>
  )
}
```

**Key Changes**:
1. **State Management**: 11 `useState` hooks instead of component properties
2. **Event Handlers**: `onInput`, `onChange` props instead of `on_*` methods
3. **Async Operations**: Direct `async/await` in `handleScrape` callback
4. **Conditional Rendering**: `{result && <...>}` instead of separate Log component
5. **Styling**: Inline `style` prop instead of CSS classes
6. **Type Safety**: Full TypeScript types for all props/state

---

### Example 2: MetricsPanel Component

**Textual (Python):**
```python
class MetricsPanel(Static):
    execution_time = reactive(0.0)
    model_used = reactive("")
    fallback_attempts = reactive(0)
    cached = reactive(False)
    validation_passed = reactive(None)

    def render(self) -> str:
        cache_text = "✓ Cached" if self.cached else "✗ Not Cached"
        validation_text = (
            "✓ Valid" if self.validation_passed
            else "✗ Invalid" if self.validation_passed is False
            else "- N/A"
        )

        return (
            f"[bold cyan]Execution Metrics[/bold cyan]\n\n"
            f"Time: [yellow]{self.execution_time:.2f}s[/yellow]\n"
            f"Model: [green]{self.model_used or 'N/A'}[/green]\n"
            f"Fallback Attempts: [magenta]{self.fallback_attempts}[/magenta]\n"
            f"Cache: [blue]{cache_text}[/blue]\n"
            f"Validation: {validation_text}"
        )
```

**TUIjoli React (TypeScript):**
```tsx
interface MetricsPanelProps {
  metadata: Metadata | null
}

function MetricsPanel({ metadata }: MetricsPanelProps) {
  if (!metadata) {
    return (
      <box style={{ border: true, borderColor: "#f59e0b", padding: 1, width: "1fr", height: 20 }}>
        <text content="No metrics yet" fg="#94a3b8" />
      </box>
    )
  }

  const cacheText = metadata.cached ? "✓ Cached" : "✗ Not Cached"
  const validationText =
    metadata.validationPassed === true ? "✓ Valid" :
    metadata.validationPassed === false ? "✗ Invalid" :
    "- N/A"

  return (
    <box style={{ border: true, borderColor: "#f59e0b", padding: 1, width: "1fr", height: 20 }}>
      <box style={{ flexDirection: "column", gap: 1 }}>
        <text content="Execution Metrics" fg="#00FFFF" attributes={TextAttributes.BOLD} />
        <text content="" /> {/* Spacer */}
        <text content={`Time: ${metadata.executionTime.toFixed(2)}s`} fg="#FFD700" />
        <text content={`Model: ${metadata.modelUsed || 'N/A'}`} fg="#00FF00" />
        <text content={`Fallback Attempts: ${metadata.fallbackAttempts}`} fg="#FF00FF" />
        <text content={`Cache: ${cacheText}`} fg="#0000FF" />
        <text content={`Validation: ${validationText}`} />
      </box>
    </box>
  )
}

interface Metadata {
  executionTime: number
  modelUsed: string
  fallbackAttempts: number
  cached: boolean
  validationPassed: boolean | null
}
```

**TUIjoli Solid (TypeScript):**
```tsx
function MetricsPanel(props: { metadata: Metadata | null }) {
  return (
    <Show
      when={props.metadata}
      fallback={
        <box style={{ border: true, borderColor: "#f59e0b", padding: 1, width: "1fr", height: 20 }}>
          <text content="No metrics yet" fg="#94a3b8" />
        </box>
      }
    >
      {(metadata) => {
        const cacheText = () => metadata().cached ? "✓ Cached" : "✗ Not Cached"
        const validationText = () =>
          metadata().validationPassed === true ? "✓ Valid" :
          metadata().validationPassed === false ? "✗ Invalid" :
          "- N/A"

        return (
          <box style={{ border: true, borderColor: "#f59e0b", padding: 1, width: "1fr", height: 20 }}>
            <box style={{ flexDirection: "column", gap: 1 }}>
              <text content="Execution Metrics" fg="#00FFFF" attributes={TextAttributes.BOLD} />
              <text content="" />
              <text content={`Time: ${metadata().executionTime.toFixed(2)}s`} fg="#FFD700" />
              <text content={`Model: ${metadata().modelUsed || 'N/A'}`} fg="#00FF00" />
              <text content={`Fallback Attempts: ${metadata().fallbackAttempts}`} fg="#FF00FF" />
              <text content={`Cache: ${cacheText()}`} fg="#0000FF" />
              <text content={`Validation: ${validationText()}`} />
            </box>
          </box>
        )
      }}
    </Show>
  )
}
```

**Key Changes**:
1. **Props-based**: Receives `metadata` as prop instead of reactive properties
2. **Null Handling**: Explicit null check with fallback UI (React: `if`, Solid: `<Show>`)
3. **Type Safety**: TypeScript interface for `Metadata`
4. **Layout**: Explicit `flexDirection: "column"` for vertical stacking
5. **Colors**: Hex colors instead of Textual's named colors

---

## 4. Refactoring Steps (Incremental Migration)

### Phase 1: Setup TypeScript Project (1 day)

**Goal**: Create TUIjoli project structure alongside existing Python code

1. **Initialize TypeScript project**:
   ```bash
   mkdir tui-ts
   cd tui-ts
   bun init
   bun add @opentui/core @opentui/react react
   # OR for Solid:
   # bun add @opentui/core @opentui/solid solid-js
   ```

2. **Configure TypeScript** (`tsconfig.json`):
   ```json
   {
     "compilerOptions": {
       "lib": ["ESNext", "DOM"],
       "target": "ESNext",
       "module": "ESNext",
       "moduleResolution": "bundler",
       "jsx": "react-jsx",
       "jsxImportSource": "@opentui/react",
       "strict": true,
       "skipLibCheck": true,
       "outDir": "./dist",
       "rootDir": "./src"
     },
     "include": ["src/**/*"],
     "exclude": ["node_modules"]
   }
   ```

3. **Port backend modules** (Python → TypeScript):
   ```
   scraper/tui_integration.py → src/backend/tui-integration.ts
   scraper/cache.py → src/backend/cache.ts
   scraper/metrics.py → src/backend/metrics.ts
   scraper/fallback.py → src/backend/fallback.ts
   # etc.
   ```

4. **Create minimal "Hello World"**:
   ```tsx
   // src/index.tsx
   import { createCliRenderer } from "@opentui/core"
   import { createRoot } from "@opentui/react"

   function App() {
     return <text content="Scrapouille TUI (TypeScript)" fg="#00FFFF" />
   }

   const renderer = await createCliRenderer({ exitOnCtrlC: true })
   createRoot(renderer).render(<App />)
   ```

5. **Test**: `bun run src/index.tsx`

---

### Phase 2: Migrate Simple Components (2-3 days)

**Goal**: Port leaf components (StatusBar, MetricsPanel, Help)

**Priority Order** (simplest → most complex):
1. ✅ **HelpTab** (static text, no state)
2. ✅ **StatusBar** (3 reactive props, simple render)
3. ✅ **MetricsPanel** (6 reactive props, conditional logic)
4. ✅ **ConfigTab** (inputs, selects, save button)

**Example: StatusBar Migration**

1. **Create component file** (`src/components/StatusBar.tsx`):
   ```tsx
   import { useState } from "react"
   import { TextAttributes } from "@opentui/core"

   interface StatusBarProps {
     statusText: string
     ollamaConnected: boolean
     redisConnected: boolean
   }

   export function StatusBar({ statusText, ollamaConnected, redisConnected }: StatusBarProps) {
     const ollamaIcon = ollamaConnected ? "🟢" : "🔴"
     const redisIcon = redisConnected ? "🟢" : "⚪"

     return (
       <box style={{
         position: "absolute",
         bottom: 0,
         width: "100%",
         height: 1,
         backgroundColor: "#1e40af",
         paddingLeft: 1,
         paddingRight: 1
       }}>
         <text
           content={`Status: ${statusText} | Ollama ${ollamaIcon} | Redis ${redisIcon}`}
           fg="#ffffff"
         />
       </box>
     )
   }
   ```

2. **Test in isolation**:
   ```tsx
   // src/tests/StatusBar.test.tsx
   function StatusBarTest() {
     return (
       <>
         <StatusBar statusText="Ready" ollamaConnected={true} redisConnected={true} />
         <StatusBar statusText="Scraping..." ollamaConnected={true} redisConnected={false} />
         <StatusBar statusText="Error" ollamaConnected={false} redisConnected={false} />
       </>
     )
   }
   ```

3. **Integrate into main App**

---

### Phase 3: Migrate Complex Components (3-5 days)

**Goal**: Port interactive tabs with async operations

**Priority Order**:
1. ✅ **SingleURLTab** (11 state vars, async scraping, form inputs)
2. ✅ **BatchTab** (progress bar, DataTable, async batch processing)
3. ✅ **MetricsTab** (DataTable, refresh button, stats display)

**Example: SingleURLTab Migration**

1. **Create component with state**:
   ```tsx
   // src/components/SingleURLTab.tsx
   import { useState, useCallback } from "react"
   import { TEMPLATES, SCHEMAS } from "../constants"
   import { useBackend } from "../hooks/useBackend"

   export function SingleURLTab({ onComplete }: SingleURLTabProps) {
     const [url, setUrl] = useState("")
     const [loading, setLoading] = useState(false)
     const backend = useBackend()

     const handleScrape = useCallback(async () => {
       // Implementation from example above...
     }, [url, /* other deps */])

     return (
       <box style={{ flexDirection: "column", gap: 1, padding: 1 }}>
         {/* UI elements... */}
       </box>
     )
   }
   ```

2. **Test async operations**:
   - Mock backend responses
   - Test loading states
   - Verify error handling

3. **Hook into App navigation**

---

### Phase 4: Build Custom Components (2-3 days)

**Goal**: Create reusable custom components for TUIjoli

**Components Needed**:
1. ✅ **CustomButton** (clickable box with hover state)
2. ✅ **Checkbox** (toggle state with checkmark)
3. ✅ **ProgressBar** (dynamic width based on progress)
4. ✅ **DataTable** (scrollable table with columns/rows)
5. ✅ **TabContainer** (tab navigation system)

**Example: CustomButton**

```tsx
// src/components/CustomButton.tsx
import { useState } from "react"

interface CustomButtonProps {
  label: string
  onClick?: () => void
  disabled?: boolean
  variant?: "default" | "primary" | "success" | "error"
}

export function CustomButton({ label, onClick, disabled = false, variant = "default" }: CustomButtonProps) {
  const [isPressed, setIsPressed] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const bgColors = {
    default: { normal: "#6b7280", hover: "#4b5563", pressed: "#374151" },
    primary: { normal: "#3b82f6", hover: "#2563eb", pressed: "#1d4ed8" },
    success: { normal: "#10b981", hover: "#059669", pressed: "#047857" },
    error: { normal: "#ef4444", hover: "#dc2626", pressed: "#b91c1c" },
  }

  const colors = bgColors[variant]
  const bgColor = disabled ? "#1f2937" :
                  isPressed ? colors.pressed :
                  isHovered ? colors.hover :
                  colors.normal

  return (
    <box
      style={{
        backgroundColor: bgColor,
        border: true,
        borderStyle: "rounded",
        padding: { top: 0, bottom: 0, left: 2, right: 2 },
        height: 3,
        minWidth: label.length + 4,
        alignItems: "center",
        justifyContent: "center",
      }}
      onMouse={(event) => {
        if (disabled) return

        switch (event.type) {
          case "down":
            setIsPressed(true)
            break
          case "up":
            setIsPressed(false)
            onClick?.()
            break
          case "over":
            setIsHovered(true)
            break
          case "out":
            setIsHovered(false)
            setIsPressed(false)
            break
        }
      }}
    >
      <text content={label} fg={disabled ? "#6b7280" : "#ffffff"} />
    </box>
  )
}
```

**Example: DataTable**

```tsx
// src/components/DataTable.tsx
import { useState } from "react"

interface DataTableProps {
  columns: string[]
  rows: string[][]
  height?: number
}

export function DataTable({ columns, rows, height = 20 }: DataTableProps) {
  const [scrollOffset, setScrollOffset] = useState(0)

  const columnWidths = columns.map((col, i) => {
    const maxContentWidth = Math.max(
      col.length,
      ...rows.map(row => (row[i]?.length || 0))
    )
    return Math.min(maxContentWidth + 2, 40) // Max 40 chars per column
  })

  const renderRow = (cells: string[], isHeader = false) => {
    return (
      <box style={{ flexDirection: "row", borderBottom: isHeader }}>
        {cells.map((cell, i) => (
          <box key={i} style={{ width: columnWidths[i], padding: { left: 1, right: 1 } }}>
            <text
              content={cell.slice(0, columnWidths[i] - 2)}
              fg={isHeader ? "#00FFFF" : "#ffffff"}
              attributes={isHeader ? TextAttributes.BOLD : undefined}
            />
          </box>
        ))}
      </box>
    )
  }

  return (
    <scrollbox
      style={{
        height,
        border: true,
        rootOptions: { backgroundColor: "#1a1b26" }
      }}
      focused
      onScroll={(offset) => setScrollOffset(offset)}
    >
      <box style={{ flexDirection: "column" }}>
        {renderRow(columns, true)}
        {rows.map((row, i) => (
          <box key={i}>
            {renderRow(row)}
          </box>
        ))}
      </box>
    </scrollbox>
  )
}
```

---

### Phase 5: Integrate App Container (1-2 days)

**Goal**: Wire all components together with tab navigation

```tsx
// src/App.tsx
import { useState, useEffect } from "react"
import { useRenderer, useKeyboard } from "@opentui/react"
import { StatusBar } from "./components/StatusBar"
import { SingleURLTab } from "./components/SingleURLTab"
import { BatchTab } from "./components/BatchTab"
import { MetricsTab } from "./components/MetricsTab"
import { ConfigTab } from "./components/ConfigTab"
import { HelpTab } from "./components/HelpTab"
import { TabContainer } from "./components/TabContainer"
import { ScraperCache, MetricsDB, TUIScraperBackend } from "./backend"

type TabName = "single" | "batch" | "metrics" | "config" | "help"

export function App() {
  const renderer = useRenderer()
  const [activeTab, setActiveTab] = useState<TabName>("single")
  const [statusText, setStatusText] = useState("Ready")
  const [ollamaConnected, setOllamaConnected] = useState(false)
  const [redisConnected, setRedisConnected] = useState(false)
  const [metadata, setMetadata] = useState<Metadata | null>(null)

  // Initialize backend
  const [backend, setBackend] = useState<TUIScraperBackend | null>(null)

  useEffect(() => {
    const initBackend = async () => {
      const cache = new ScraperCache({ enabled: true, defaultTTLHours: 24 })
      setRedisConnected(cache.enabled)

      const metricsDB = new MetricsDB("data/metrics.db")
      const backendInstance = new TUIScraperBackend(cache, metricsDB)
      setBackend(backendInstance)

      const connected = await backendInstance.checkOllamaConnection()
      setOllamaConnected(connected)
      setStatusText("Ready - Press Ctrl+Q to quit")
    }

    initBackend()
  }, [])

  // Keyboard shortcuts
  useKeyboard((key) => {
    if (key.name === "t" && key.ctrl) {
      const tabs: TabName[] = ["single", "batch", "metrics", "config", "help"]
      const currentIndex = tabs.indexOf(activeTab)
      const nextIndex = (currentIndex + 1) % tabs.length
      setActiveTab(tabs[nextIndex])
    }
  })

  if (!backend) {
    return <text content="Initializing..." />
  }

  const tabs = [
    { id: "single", label: "Single URL" },
    { id: "batch", label: "Batch" },
    { id: "metrics", label: "Metrics" },
    { id: "config", label: "Config" },
    { id: "help", label: "Help" },
  ]

  return (
    <box style={{ flexDirection: "column", height: "100%" }}>
      {/* Header */}
      <box style={{ height: 1, backgroundColor: "#1e40af" }}>
        <text content="Scrapouille TUI v3.0" fg="#00FFFF" attributes={TextAttributes.BOLD} />
      </box>

      {/* Tab Navigation */}
      <TabContainer tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Content Area */}
      <box style={{ flexGrow: 1, overflow: "scroll" }}>
        {activeTab === "single" && (
          <SingleURLTab
            backend={backend}
            onComplete={(result, meta) => {
              setMetadata(meta)
              setStatusText("Scraping completed")
            }}
            onStatusChange={setStatusText}
          />
        )}
        {activeTab === "batch" && (
          <BatchTab backend={backend} onStatusChange={setStatusText} />
        )}
        {activeTab === "metrics" && (
          <MetricsTab backend={backend} />
        )}
        {activeTab === "config" && (
          <ConfigTab />
        )}
        {activeTab === "help" && (
          <HelpTab />
        )}
      </box>

      {/* Status Bar */}
      <StatusBar
        statusText={statusText}
        ollamaConnected={ollamaConnected}
        redisConnected={redisConnected}
      />

      {/* Footer */}
      <box style={{ height: 1, backgroundColor: "#374151" }}>
        <text content="Ctrl+Q: Quit | Ctrl+T: Switch Tab" fg="#9ca3af" />
      </box>
    </box>
  )
}
```

---

### Phase 6: Testing & Debugging (2-3 days)

**Goal**: Ensure feature parity with Python version

**Test Coverage**:
1. ✅ **Component Tests**:
   - Each component renders correctly
   - Props propagate as expected
   - Event handlers fire correctly

2. ✅ **Integration Tests**:
   - Single URL scraping flow
   - Batch processing flow
   - Metrics refresh flow
   - Cache hit/miss scenarios

3. ✅ **Performance Tests**:
   - Startup time: <100ms (vs 3-5s Textual)
   - Memory usage: <15MB (vs ~50MB Textual)
   - Rendering: 60fps

**Testing Tools**:
```bash
# Unit tests (Vitest or Jest)
bun add -d vitest @testing-library/react

# Integration tests (Playwright for TUI)
bun add -d @playwright/test
```

**Example Test**:
```tsx
// src/components/__tests__/StatusBar.test.tsx
import { describe, it, expect } from "vitest"
import { render } from "@testing-library/react"
import { StatusBar } from "../StatusBar"

describe("StatusBar", () => {
  it("renders status text and connection icons", () => {
    const { container } = render(
      <StatusBar
        statusText="Ready"
        ollamaConnected={true}
        redisConnected={false}
      />
    )

    expect(container.textContent).toContain("Status: Ready")
    expect(container.textContent).toContain("🟢") // Ollama connected
    expect(container.textContent).toContain("⚪") // Redis disconnected
  })
})
```

---

### Phase 7: Deployment & Documentation (1 day)

**Goal**: Package and ship TypeScript TUI

1. **Build script** (`package.json`):
   ```json
   {
     "scripts": {
       "dev": "bun run src/index.tsx",
       "build": "bun build src/index.tsx --outdir dist --target bun",
       "start": "bun dist/index.js",
       "test": "vitest run",
       "test:watch": "vitest"
     }
   }
   ```

2. **Create executable**:
   ```bash
   # Option 1: Bun executable
   bun build src/index.tsx --compile --outfile scrapouille-tui

   # Option 2: Node.js bundle
   bun build src/index.tsx --target node --outfile dist/index.js
   ```

3. **Update documentation**:
   ```markdown
   # TUI-TS-README.md

   ## Running TypeScript TUI

   ### Development:
   ```bash
   bun run dev
   ```

   ### Production:
   ```bash
   bun run build
   bun run start
   # Or: ./scrapouille-tui (if compiled)
   ```

   ### Aliases:
   ```bash
   alias stui-ts="bun run /path/to/tui-ts/src/index.tsx"
   ```
   ```

---

## 5. Testing Strategy

### 5.1 Unit Tests (Component-Level)

**Goal**: Verify individual components render and behave correctly

**Framework**: Vitest + Testing Library

```tsx
// src/components/__tests__/CustomButton.test.tsx
import { describe, it, expect, vi } from "vitest"
import { render, fireEvent } from "@testing-library/react"
import { CustomButton } from "../CustomButton"

describe("CustomButton", () => {
  it("renders label", () => {
    const { getByText } = render(<CustomButton label="Click Me" />)
    expect(getByText("Click Me")).toBeTruthy()
  })

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn()
    const { getByText } = render(<CustomButton label="Click" onClick={onClick} />)

    fireEvent.click(getByText("Click"))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it("disables button when disabled prop is true", () => {
    const onClick = vi.fn()
    const { getByText } = render(<CustomButton label="Click" onClick={onClick} disabled />)

    fireEvent.click(getByText("Click"))
    expect(onClick).not.toHaveBeenCalled()
  })

  it("applies correct variant styling", () => {
    const { rerender, container } = render(<CustomButton label="Test" variant="primary" />)
    expect(container.firstChild).toHaveStyle({ backgroundColor: "#3b82f6" })

    rerender(<CustomButton label="Test" variant="error" />)
    expect(container.firstChild).toHaveStyle({ backgroundColor: "#ef4444" })
  })
})
```

---

### 5.2 Integration Tests (Flow-Level)

**Goal**: Verify complete user workflows (e.g., scraping, batch processing)

**Framework**: Vitest + Mock Backend

```tsx
// src/tests/integration/scraping-flow.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, waitFor } from "@testing-library/react"
import { App } from "../../App"
import { mockBackend } from "../mocks/backend"

describe("Single URL Scraping Flow", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("completes full scraping workflow", async () => {
    mockBackend.scrapeSingleURL.mockResolvedValue({
      result: { title: "Test Title", content: "Test content" },
      metadata: {
        executionTime: 2.5,
        modelUsed: "qwen2.5-coder:7b",
        fallbackAttempts: 0,
        cached: false,
        validationPassed: true,
      }
    })

    const { getByPlaceholderText, getByText, findByText } = render(<App />)

    // 1. Enter URL
    const urlInput = getByPlaceholderText("https://example.com")
    fireEvent.input(urlInput, { target: { value: "https://test.com" } })

    // 2. Enter prompt
    const promptInput = getByPlaceholderText("Enter custom prompt...")
    fireEvent.input(promptInput, { target: { value: "Extract title and content" } })

    // 3. Click Scrape
    const scrapeButton = getByText("Scrape")
    fireEvent.click(scrapeButton)

    // 4. Wait for results
    await waitFor(() => {
      expect(mockBackend.scrapeSingleURL).toHaveBeenCalledWith({
        url: "https://test.com",
        prompt: "Extract title and content",
        model: "qwen2.5-coder:7b",
        // ... other params
      })
    })

    // 5. Verify results displayed
    const resultsText = await findByText(/Test Title/)
    expect(resultsText).toBeTruthy()

    // 6. Verify metrics updated
    const metricsText = await findByText(/Time: 2.50s/)
    expect(metricsText).toBeTruthy()
  })

  it("handles scraping errors gracefully", async () => {
    mockBackend.scrapeSingleURL.mockRejectedValue(new Error("Network error"))

    const { getByPlaceholderText, getByText, findByText } = render(<App />)

    // ... similar setup

    fireEvent.click(getByText("Scrape"))

    const errorText = await findByText(/Error: Network error/)
    expect(errorText).toBeTruthy()
  })
})
```

---

### 5.3 Visual Regression Tests (Optional)

**Goal**: Catch unintended UI changes

**Framework**: Playwright + Snapshot Testing

```tsx
// src/tests/visual/snapshots.test.ts
import { test, expect } from "@playwright/test"

test("StatusBar renders correctly", async ({ page }) => {
  await page.goto("http://localhost:3000")

  const statusBar = page.locator("#status-bar")
  await expect(statusBar).toHaveScreenshot("status-bar.png")
})

test("SingleURLTab renders correctly", async ({ page }) => {
  await page.goto("http://localhost:3000")

  const singleTab = page.locator("#tab-single")
  await expect(singleTab).toHaveScreenshot("single-url-tab.png")
})
```

---

## 6. Common Pitfalls & Solutions

### Pitfall 1: Reactive Properties vs React State

**Problem**: Textual's `reactive` properties auto-trigger re-renders. React/Solid require explicit state setters.

**Textual**:
```python
class MyComponent(Static):
    count = reactive(0)

    def increment(self):
        self.count += 1  # Auto re-renders
```

**TUIjoli (Wrong)**:
```tsx
function MyComponent() {
  const [count, setCount] = useState(0)

  const increment = () => {
    count += 1  // ❌ WRONG: Doesn't trigger re-render
  }
}
```

**TUIjoli (Correct)**:
```tsx
function MyComponent() {
  const [count, setCount] = useState(0)

  const increment = () => {
    setCount(count + 1)  // ✅ CORRECT: Triggers re-render
    // Or: setCount(prev => prev + 1)
  }
}
```

---

### Pitfall 2: Async Event Handlers

**Problem**: Textual uses `asyncio.create_task()`. TUIjoli uses standard async/await.

**Textual**:
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    asyncio.create_task(self._async_handler())

async def _async_handler(self):
    result = await fetch_data()
```

**TUIjoli (Wrong)**:
```tsx
function MyComponent() {
  const handleClick = async () => {
    const result = await fetchData()  // ❌ BLOCKS UI
  }
}
```

**TUIjoli (Correct)**:
```tsx
function MyComponent() {
  const [loading, setLoading] = useState(false)

  const handleClick = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetchData()  // ✅ Non-blocking with loading state
      // ... use result
    } finally {
      setLoading(false)
    }
  }, [])

  return <button onClick={handleClick} disabled={loading}>
    {loading ? "Loading..." : "Click"}
  </button>
}
```

---

### Pitfall 3: Direct Child Manipulation

**Problem**: Textual allows direct child manipulation via `query_one()`. TUIjoli requires props/context.

**Textual**:
```python
def update_metrics(self):
    panel = self.query_one("#metrics_panel", MetricsPanel)
    panel.execution_time = 5.2  # Direct mutation
```

**TUIjoli (Wrong)**:
```tsx
function App() {
  const panelRef = useRef<HTMLElement>(null)

  const updateMetrics = () => {
    panelRef.current.executionTime = 5.2  // ❌ WRONG: Anti-pattern
  }
}
```

**TUIjoli (Correct - Props)**:
```tsx
function App() {
  const [executionTime, setExecutionTime] = useState(0)

  const updateMetrics = () => {
    setExecutionTime(5.2)  // ✅ Update state, re-render child
  }

  return <MetricsPanel executionTime={executionTime} />
}
```

**TUIjoli (Correct - Context)**:
```tsx
const MetricsContext = createContext<MetricsContextType>(null)

function App() {
  const [executionTime, setExecutionTime] = useState(0)

  return (
    <MetricsContext.Provider value={{ executionTime, setExecutionTime }}>
      <SomeParent />
      <MetricsPanel />
    </MetricsContext.Provider>
  )
}

function MetricsPanel() {
  const { executionTime } = useContext(MetricsContext)
  return <text content={`Time: ${executionTime}s`} />
}
```

---

### Pitfall 4: CSS Styling Translation

**Problem**: Textual uses CSS classes. TUIjoli uses inline styles.

**Textual**:
```python
CSS = """
.results-container {
    width: 2fr;
    height: 20;
    border: solid $primary;
    margin: 1 1 0 0;
}
"""
```

**TUIjoli (Correct)**:
```tsx
const resultsContainerStyle = {
  width: "2fr",  // Or: width: "66%" for flexbox
  height: 20,
  border: true,
  borderColor: "#3b82f6",  // $primary equivalent
  margin: { top: 0, right: 0, bottom: 1, left: 1 },
}

<box style={resultsContainerStyle}>
  <ResultsDisplay />
</box>
```

**CSS Variables Translation**:
- `$primary` → `#3b82f6` (blue)
- `$accent` → `#f59e0b` (orange)
- `$surface` → `#1a1b26` (dark bg)
- `$text` → `#ffffff` (white)

---

### Pitfall 5: Event Propagation

**Problem**: Textual and TUIjoli handle event bubbling differently.

**Textual**:
```python
def on_mouse_down(self, event: MouseEvent) -> None:
    event.stop()  # Stop propagation
```

**TUIjoli (Correct)**:
```tsx
<box
  onMouse={(event) => {
    if (event.type === "down") {
      event.stopPropagation()  // ✅ Stop bubbling
      handleClick()
    }
  }}
>
  <text content="Click me" />
</box>
```

---

### Pitfall 6: Ref Access Timing

**Problem**: Refs may be `null` on first render.

**TUIjoli (Wrong)**:
```tsx
function MyComponent() {
  const inputRef = useRef<InputRenderable>(null)

  useEffect(() => {
    inputRef.current.focus()  // ❌ May be null
  }, [])
}
```

**TUIjoli (Correct)**:
```tsx
function MyComponent() {
  const inputRef = useRef<InputRenderable>(null)

  useEffect(() => {
    if (inputRef.current) {  // ✅ Null check
      inputRef.current.focus()
    }
  }, [])

  // Or use callback ref:
  const inputCallbackRef = useCallback((node: InputRenderable | null) => {
    if (node) {
      node.focus()  // ✅ Guaranteed non-null
    }
  }, [])

  return <input ref={inputCallbackRef} />
}
```

---

## 7. Performance Optimization Tips

### 7.1 Memoization (React)

**Problem**: Expensive computations re-run on every render.

**Solution**: `useMemo` and `useCallback`

```tsx
function MetricsPanel({ data }: { data: ScrapeMetric[] }) {
  // ❌ BAD: Recalculates on every render
  const avgTime = data.reduce((sum, m) => sum + m.executionTime, 0) / data.length

  // ✅ GOOD: Only recalculates when data changes
  const avgTime = useMemo(() => {
    return data.reduce((sum, m) => sum + m.executionTime, 0) / data.length
  }, [data])

  // ❌ BAD: New function on every render
  const handleRefresh = () => { fetchMetrics() }

  // ✅ GOOD: Stable function reference
  const handleRefresh = useCallback(() => {
    fetchMetrics()
  }, [])
}
```

---

### 7.2 Component Splitting (React & Solid)

**Problem**: Large component re-renders even when only part of state changes.

**Solution**: Split into smaller components

```tsx
// ❌ BAD: Entire form re-renders on URL change
function SingleURLTab() {
  const [url, setUrl] = useState("")
  const [prompt, setPrompt] = useState("")
  const [schema, setSchema] = useState<string | null>(null)
  // ... 10 more state vars

  return (
    <box>
      <input value={url} onInput={setUrl} />
      <textarea value={prompt} onInput={setPrompt} />
      <select value={schema} onChange={setSchema} />
      {/* ... */}
      <ExpensiveResultsDisplay results={results} />
    </box>
  )
}

// ✅ GOOD: Split into focused components
function SingleURLTab() {
  const [config, setConfig] = useState<ScrapeConfig>({})
  const [results, setResults] = useState(null)

  return (
    <box>
      <ScrapeConfigForm config={config} onChange={setConfig} />
      <ResultsDisplay results={results} />
    </box>
  )
}

// Only re-renders when config changes
function ScrapeConfigForm({ config, onChange }: ConfigFormProps) {
  const [localUrl, setLocalUrl] = useState(config.url)
  // ... local state
}

// Only re-renders when results change (React.memo)
const ResultsDisplay = React.memo(({ results }: { results: any }) => {
  // ... expensive rendering
})
```

---

### 7.3 Lazy Loading (React)

**Problem**: All tabs loaded on mount, increasing startup time.

**Solution**: `React.lazy` + `Suspense`

```tsx
import { lazy, Suspense } from "react"

const SingleURLTab = lazy(() => import("./components/SingleURLTab"))
const BatchTab = lazy(() => import("./components/BatchTab"))
const MetricsTab = lazy(() => import("./components/MetricsTab"))

function App() {
  const [activeTab, setActiveTab] = useState("single")

  return (
    <box>
      <Suspense fallback={<text content="Loading..." />}>
        {activeTab === "single" && <SingleURLTab />}
        {activeTab === "batch" && <BatchTab />}
        {activeTab === "metrics" && <MetricsTab />}
      </Suspense>
    </box>
  )
}
```

---

### 7.4 Solid's Fine-Grained Reactivity

**Advantage**: Solid only re-renders affected parts, no memoization needed.

```tsx
// React: Entire component re-renders
function MetricsPanel() {
  const [time, setTime] = useState(0)
  const [model, setModel] = useState("")

  return (
    <box>
      <text content={`Time: ${time}s`} />  {/* Re-renders on model change */}
      <text content={`Model: ${model}`} />  {/* Re-renders on time change */}
    </box>
  )
}

// Solid: Only affected <text> re-renders
function MetricsPanel() {
  const [time, setTime] = createSignal(0)
  const [model, setModel] = createSignal("")

  return (
    <box>
      <text content={`Time: ${time()}s`} />  {/* ✅ Only re-renders on time() change */}
      <text content={`Model: ${model()}`} />  {/* ✅ Only re-renders on model() change */}
    </box>
  )
}
```

**Recommendation**: Use Solid for better out-of-the-box performance, React for larger ecosystem.

---

## 8. Final Comparison: Textual vs TUIjoli

| Aspect | Textual (Python) | TUIjoli (React) | TUIjoli (Solid) |
|--------|------------------|-----------------|-----------------|
| **Language** | Python | TypeScript | TypeScript |
| **Paradigm** | Class-based OOP | Functional components | Functional components |
| **State Management** | `reactive` properties | `useState` hooks | `createSignal` |
| **Lifecycle** | `on_mount()`, `on_unmount()` | `useEffect()` | `onMount()`, `onCleanup()` |
| **Event Handling** | `on_*` methods | Props (`onClick`, `onMouse`) | Props (`onClick`, `onMouse`) |
| **Styling** | CSS classes | Inline `style` prop | Inline `style` prop |
| **Async** | `asyncio` | Promises + async/await | Promises + async/await |
| **Re-rendering** | Auto on `reactive` change | Full component tree | Fine-grained (only affected parts) |
| **Bundle Size** | ~50MB (Python + deps) | ~15MB (Bun runtime) | ~15MB (Bun runtime) |
| **Startup Time** | 3-5s | <100ms | <100ms |
| **Memory Usage** | ~50MB | ~15MB | ~15MB |
| **Ecosystem** | Limited TUI packages | Vast NPM ecosystem | Vast NPM ecosystem |
| **Type Safety** | Optional (mypy) | Built-in (TypeScript) | Built-in (TypeScript) |
| **Testing** | pytest | Vitest + Testing Library | Vitest + Testing Library |
| **Learning Curve** | Medium (Python + Textual API) | Medium (React patterns) | Low-Medium (simpler than React) |

---

## 9. Recommended Approach

**For Scrapouille Migration**:

### Option A: React (Recommended for Teams)

**Pros**:
- Larger ecosystem (more libraries, tutorials, community support)
- Familiar to most TypeScript developers
- Better tooling (React DevTools, extensive testing libraries)
- Easier to hire developers with React experience

**Cons**:
- More boilerplate (`useCallback`, `useMemo` for optimization)
- Virtual DOM overhead (still fast for TUI, but not as efficient as Solid)

**Best For**:
- Teams with React experience
- Projects requiring extensive third-party integrations
- Longer-term maintenance by multiple developers

---

### Option B: Solid (Recommended for Performance)

**Pros**:
- **10-100x faster re-renders** than React (fine-grained reactivity)
- Smaller bundle size (~50% of React)
- Less boilerplate (no need for `useCallback`, `useMemo`)
- Simpler mental model (signals vs hooks)

**Cons**:
- Smaller ecosystem (fewer libraries, less community support)
- Steeper learning curve for devs unfamiliar with reactive programming
- Less mature tooling

**Best For**:
- Solo developers or small teams
- Performance-critical applications
- Projects where bundle size matters

---

### Recommended Timeline: **React Migration (10-12 days)**

**Day 1**: Setup TypeScript project, port backend modules
**Day 2-3**: Migrate simple components (StatusBar, MetricsPanel, HelpTab)
**Day 4-6**: Migrate complex components (SingleURLTab, BatchTab, MetricsTab)
**Day 7-8**: Build custom components (Button, Checkbox, DataTable, ProgressBar)
**Day 9-10**: Integrate App container, wire all components
**Day 11**: Testing, debugging, performance optimization
**Day 12**: Documentation, deployment, final polish

---

## 10. Next Steps

1. **Choose framework**: React (ecosystem) or Solid (performance)
2. **Setup repo**: `mkdir tui-ts && cd tui-ts && bun init`
3. **Install deps**: `bun add @opentui/core @opentui/react react` (or `@opentui/solid solid-js`)
4. **Create minimal app**: Verify TUIjoli works on your system
5. **Follow Phase 1**: Port backend modules (cache, metrics, fallback)
6. **Follow Phase 2-7**: Incremental component migration
7. **Test**: Ensure feature parity with Python version
8. **Deploy**: Build executable, update aliases/scripts

---

## Appendix: Quick Reference

### Textual → TUIjoli Cheat Sheet

| Textual | TUIjoli (React/Solid) |
|---------|----------------------|
| `App` | `createCliRenderer()` + `createRoot()` |
| `Static`, `Label` | `<text>` |
| `Input` | `<input>` |
| `TextArea` | `<textarea>` |
| `Select` | `<select>` |
| `Button` | Custom `<box>` + `onMouse` |
| `Container`, `Horizontal`, `VerticalScroll` | `<box>` + `style` |
| `reactive("value")` | `useState("value")` / `createSignal("value")` |
| `self.query_one("#id")` | `useRef()` / Solid refs |
| `on_mount()` | `useEffect(() => {}, [])` / `onMount()` |
| `on_button_pressed()` | `<button onClick={handler}>` |
| `asyncio.create_task()` | `async/await` in handlers |
| `CSS = "..."` | `style={{ ... }}` prop |

---

**End of Migration Guide** 🚀

For questions or issues, refer to:
- TUIjoli Docs: https://github.com/BasicFist/TUIjoli
- React Docs: https://react.dev
- Solid Docs: https://solidjs.com
- Scrapouille CLAUDE.md: Project-specific context
