# Textual ↔ TUIjoli Quick Reference Cheat Sheet

**For**: Rapid lookup during migration
**Version**: Scrapouille v3.0 → TUIjoli
**Print**: Single-page reference

---

## 1. Component Equivalents

| Textual | TUIjoli | Example |
|---------|---------|---------|
| `App` | `createCliRenderer()` | `const renderer = await createCliRenderer()` |
| `Static` | `<text>` | `<text content="Hello" />` |
| `Label` | `<text>` | `<text content="Label:" />` |
| `Input` | `<input>` | `<input placeholder="..." onInput={fn} />` |
| `TextArea` | `<textarea>` | `<textarea onInput={fn} />` |
| `Button` | Custom `<box>` | See Custom Button below |
| `Select` | `<select>` | `<select options={[...]} onChange={fn} />` |
| `Checkbox` | Custom | See Custom Checkbox below |
| `DataTable` | Custom | See Custom DataTable below |
| `ProgressBar` | Custom | See Custom ProgressBar below |
| `Log` | `<scrollbox>` + `<text>` | `<scrollbox><text content={log} /></scrollbox>` |
| `Container` | `<box>` | `<box flexDirection="column">{children}</box>` |
| `Horizontal` | `<box>` | `<box flexDirection="row">{children}</box>` |
| `VerticalScroll` | `<box>` | `<box overflow="scroll">{children}</box>` |
| `TabbedContent` | Custom tabs | See Tab System below |
| `Header` | `<box>` | `<box position="absolute" top={0} />` |
| `Footer` | `<box>` | `<box position="absolute" bottom={0} />` |

---

## 2. State Management

### Textual (Python)
```python
class MyComponent(Static):
    count = reactive(0)
    text = reactive("Hello")
```

### React (TypeScript)
```tsx
function MyComponent() {
  const [count, setCount] = useState(0)
  const [text, setText] = useState("Hello")
}
```

### Solid (TypeScript)
```tsx
function MyComponent() {
  const [count, setCount] = createSignal(0)
  const [text, setText] = createSignal("Hello")
  // Access: count(), text()
}
```

---

## 3. Lifecycle Hooks

### Textual
```python
async def on_mount(self) -> None:
    self.cache = ScraperCache()

def on_unmount(self) -> None:
    self.cache.close()
```

### React
```tsx
useEffect(() => {
  const cache = new ScraperCache()
  return () => cache.close()  // Cleanup
}, [])  // Empty deps = mount/unmount only
```

### Solid
```tsx
onMount(() => {
  const cache = new ScraperCache()
  // Setup...
})

onCleanup(() => {
  cache.close()
})
```

---

## 4. Event Handling

### Textual
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    button_id = event.button.id
    if button_id == "my_button":
        self.handle_click()
```

### React/Solid
```tsx
<CustomButton
  id="my-button"
  onClick={handleClick}
  label="Click me"
/>
```

---

## 5. Async Operations

### Textual
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    asyncio.create_task(self._async_handler())

async def _async_handler(self):
    result = await fetch_data()
```

### React
```tsx
const [loading, setLoading] = useState(false)

const handleClick = useCallback(async () => {
  setLoading(true)
  try {
    const result = await fetchData()
  } finally {
    setLoading(false)
  }
}, [])
```

### Solid
```tsx
const [loading, setLoading] = createSignal(false)

const handleClick = async () => {
  setLoading(true)
  try {
    const result = await fetchData()
  } finally {
    setLoading(false)
  }
}
```

---

## 6. Parent-Child Communication

### Textual (Direct Mutation)
```python
def update_child(self):
    child = self.query_one("#child", MyComponent)
    child.value = "new value"
```

### React (Props)
```tsx
function Parent() {
  const [value, setValue] = useState("")
  return <Child value={value} onChange={setValue} />
}

function Child({ value, onChange }: ChildProps) {
  return <input value={value} onInput={onChange} />
}
```

### React (Context)
```tsx
const MyContext = createContext<ContextType>(null)

function Parent() {
  const [value, setValue] = useState("")
  return (
    <MyContext.Provider value={{ value, setValue }}>
      <Child />
    </MyContext.Provider>
  )
}

function Child() {
  const { value, setValue } = useContext(MyContext)!
  return <input value={value} onInput={setValue} />
}
```

---

## 7. Styling

### Textual (CSS)
```python
CSS = """
.my-box {
    width: 40;
    height: 10;
    border: solid $primary;
    margin: 1 0;
    background: $surface;
}
"""
```

### TUIjoli (Inline Styles)
```tsx
<box style={{
  width: 40,
  height: 10,
  border: true,
  borderColor: "#3b82f6",  // $primary
  margin: { top: 1, bottom: 0, left: 1, right: 0 },
  backgroundColor: "#1a1b26"  // $surface
}}>
```

**Color Mapping**:
- `$primary` → `#3b82f6` (blue)
- `$accent` → `#f59e0b` (orange)
- `$surface` → `#1a1b26` (dark)
- `$text` → `#ffffff` (white)

---

## 8. Conditional Rendering

### Textual
```python
def render(self) -> str:
    if self.loading:
        return "Loading..."
    return f"Data: {self.data}"
```

### React
```tsx
{loading ? (
  <text content="Loading..." />
) : (
  <text content={`Data: ${data}`} />
)}

// Or with &&:
{data && <ResultsDisplay data={data} />}
```

### Solid
```tsx
<Show
  when={!loading()}
  fallback={<text content="Loading..." />}
>
  <text content={`Data: ${data()}`} />
</Show>

// Or with &&:
{data() && <ResultsDisplay data={data()!} />}
```

---

## 9. Lists & Iteration

### Textual
```python
def compose(self) -> ComposeResult:
    for item in self.items:
        yield Label(item.name)
```

### React
```tsx
{items.map((item, i) => (
  <text key={i} content={item.name} />
))}
```

### Solid
```tsx
<For each={items()}>
  {(item, i) => <text content={item.name} />}
</For>

// Or simple map:
{items().map((item, i) => (
  <text content={item.name} />
))}
```

---

## 10. Refs (Direct Element Access)

### Textual
```python
input = self.query_one("#my_input", Input)
input.value = "new value"
input.focus()
```

### React
```tsx
const inputRef = useRef<InputRenderable>(null)

useEffect(() => {
  if (inputRef.current) {
    inputRef.current.value = "new value"
    inputRef.current.focus()
  }
}, [])

<input ref={inputRef} />
```

### Solid
```tsx
let inputRef: InputRenderable | undefined

onMount(() => {
  if (inputRef) {
    inputRef.value = "new value"
    inputRef.focus()
  }
})

<input ref={inputRef} />
```

---

## 11. Custom Components

### Custom Button

```tsx
import { useState } from "react"

interface ButtonProps {
  label: string
  onClick?: () => void
  disabled?: boolean
  variant?: "default" | "primary" | "success" | "error"
}

export function CustomButton({ label, onClick, disabled = false, variant = "default" }: ButtonProps) {
  const [isPressed, setIsPressed] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const colors = {
    default: { normal: "#6b7280", hover: "#4b5563" },
    primary: { normal: "#3b82f6", hover: "#2563eb" },
    success: { normal: "#10b981", hover: "#059669" },
    error: { normal: "#ef4444", hover: "#dc2626" },
  }

  const bgColor = disabled ? "#1f2937" :
                  isPressed ? colors[variant].hover :
                  isHovered ? colors[variant].hover :
                  colors[variant].normal

  return (
    <box
      style={{
        backgroundColor: bgColor,
        border: true,
        borderStyle: "rounded",
        padding: { top: 0, bottom: 0, left: 2, right: 2 },
        height: 3,
      }}
      onMouse={(event) => {
        if (disabled) return
        if (event.type === "down") setIsPressed(true)
        if (event.type === "up") { setIsPressed(false); onClick?.() }
        if (event.type === "over") setIsHovered(true)
        if (event.type === "out") { setIsHovered(false); setIsPressed(false) }
      }}
    >
      <text content={label} fg={disabled ? "#6b7280" : "#ffffff"} />
    </box>
  )
}
```

---

### Custom Checkbox

```tsx
interface CheckboxProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

export function Checkbox({ label, checked, onChange, disabled = false }: CheckboxProps) {
  const icon = checked ? "☑" : "☐"

  return (
    <box
      style={{ flexDirection: "row", gap: 1 }}
      onMouse={(event) => {
        if (!disabled && event.type === "down") {
          onChange(!checked)
        }
      }}
    >
      <text content={icon} fg={disabled ? "#6b7280" : "#3b82f6"} />
      <text content={label} fg={disabled ? "#6b7280" : "#ffffff"} />
    </box>
  )
}
```

---

### Custom ProgressBar

```tsx
interface ProgressBarProps {
  progress: number  // 0-100
  total: number
  height?: number
}

export function ProgressBar({ progress, total, height = 1 }: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (progress / total) * 100))

  return (
    <box style={{ flexDirection: "column", gap: 0 }}>
      <text content={`${progress}/${total} (${percentage.toFixed(1)}%)`} />
      <box style={{ width: "100%", height, backgroundColor: "#374151", border: true }}>
        <box style={{ width: `${percentage}%`, height, backgroundColor: "#3b82f6" }} />
      </box>
    </box>
  )
}
```

---

### Tab System

```tsx
interface Tab {
  id: string
  label: string
}

interface TabContainerProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
}

export function TabContainer({ tabs, activeTab, onTabChange }: TabContainerProps) {
  return (
    <box style={{ flexDirection: "row", height: 3, borderBottom: true }}>
      {tabs.map((tab) => (
        <box
          key={tab.id}
          style={{
            padding: { top: 0, bottom: 0, left: 2, right: 2 },
            backgroundColor: activeTab === tab.id ? "#3b82f6" : "#1f2937",
            border: true,
            borderStyle: "rounded",
          }}
          onMouse={(event) => {
            if (event.type === "down") onTabChange(tab.id)
          }}
        >
          <text
            content={tab.label}
            fg={activeTab === tab.id ? "#ffffff" : "#9ca3af"}
            attributes={activeTab === tab.id ? TextAttributes.BOLD : undefined}
          />
        </box>
      ))}
    </box>
  )
}
```

---

## 12. Keyboard Shortcuts

### Textual
```python
BINDINGS = [
    Binding("ctrl+q", "quit", "Quit"),
    Binding("ctrl+t", "switch_tab", "Switch Tab"),
]

def action_quit(self) -> None:
    self.exit()
```

### React
```tsx
import { useKeyboard } from "@opentui/react"

useKeyboard((key) => {
  if (key.name === "q" && key.ctrl) {
    process.exit(0)
  }
  if (key.name === "t" && key.ctrl) {
    switchTab()
  }
})
```

### Solid
```tsx
import { useKeyboard } from "@opentui/solid"

useKeyboard((key) => {
  if (key.name === "q" && key.ctrl) {
    process.exit(0)
  }
  if (key.name === "t" && key.ctrl) {
    switchTab()
  }
})
```

---

## 13. Common Mistakes

### ❌ Mistake 1: Mutating State Directly
```tsx
// WRONG
const [count, setCount] = useState(0)
count += 1

// CORRECT
setCount(count + 1)
// Or: setCount(prev => prev + 1)
```

---

### ❌ Mistake 2: Missing Dependencies
```tsx
// WRONG
useEffect(() => {
  console.log(url)
}, [])  // ❌ Missing 'url' dependency

// CORRECT
useEffect(() => {
  console.log(url)
}, [url])  // ✅ Includes all used variables
```

---

### ❌ Mistake 3: Async useEffect
```tsx
// WRONG
useEffect(async () => {
  await fetchData()
}, [])  // ❌ useEffect can't be async

// CORRECT
useEffect(() => {
  const fetchAsync = async () => {
    await fetchData()
  }
  fetchAsync()
}, [])  // ✅ Async inside sync
```

---

### ❌ Mistake 4: Forgetting to Call Solid Signals
```tsx
// WRONG (Solid)
const [count, setCount] = createSignal(0)
console.log(count)  // ❌ Logs function, not value

// CORRECT (Solid)
console.log(count())  // ✅ Calls getter function
```

---

## 14. Performance Tips

### React Optimization
```tsx
// Memoize expensive computations
const avgTime = useMemo(() => {
  return data.reduce((sum, m) => sum + m.time, 0) / data.length
}, [data])

// Memoize callbacks
const handleClick = useCallback(() => {
  doSomething()
}, [])

// Memoize components
const ExpensiveComponent = React.memo(({ data }) => {
  // ... expensive rendering
})
```

### Solid (No Optimization Needed)
```tsx
// Solid automatically optimizes, no useMemo/useCallback needed
const avgTime = () => {
  return data().reduce((sum, m) => sum + m.time, 0) / data().length
}

const handleClick = () => {
  doSomething()
}
```

---

## 15. Testing

### Component Test (Vitest)
```tsx
import { describe, it, expect, vi } from "vitest"
import { render, fireEvent } from "@testing-library/react"
import { CustomButton } from "../CustomButton"

describe("CustomButton", () => {
  it("calls onClick when clicked", () => {
    const onClick = vi.fn()
    const { getByText } = render(<CustomButton label="Click" onClick={onClick} />)

    fireEvent.click(getByText("Click"))
    expect(onClick).toHaveBeenCalledTimes(1)
  })
})
```

---

## 16. Quick Setup

### Initialize Project
```bash
mkdir tui-ts && cd tui-ts
bun init

# React
bun add @opentui/core @opentui/react react

# Solid
bun add @opentui/core @opentui/solid solid-js
```

### tsconfig.json (React)
```json
{
  "compilerOptions": {
    "lib": ["ESNext", "DOM"],
    "jsx": "react-jsx",
    "jsxImportSource": "@opentui/react",
    "strict": true
  }
}
```

### tsconfig.json (Solid)
```json
{
  "compilerOptions": {
    "lib": ["ESNext", "DOM"],
    "jsx": "preserve",
    "jsxImportSource": "@opentui/solid",
    "strict": true
  }
}
```

### Minimal App (React)
```tsx
import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"

function App() {
  return <text content="Hello, TUIjoli!" fg="#00FFFF" />
}

const renderer = await createCliRenderer({ exitOnCtrlC: true })
createRoot(renderer).render(<App />)
```

### Run
```bash
bun run src/index.tsx
```

---

**Print this page for quick reference during migration!** 📄

**Full Guide**: `TEXTUAL-TO-TUIJOLI-MIGRATION-GUIDE.md` (86 pages)
**Summary**: `MIGRATION-EXECUTIVE-SUMMARY.md` (8 pages)
