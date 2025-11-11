# Textual → TUIjoli Migration: Executive Summary

**Project**: Scrapouille v3.0 TUI Migration
**Prepared**: 2025-11-11
**Estimated Effort**: 10-12 days (React) or 8-10 days (Solid)

---

## Why Migrate?

### Performance Gains

| Metric | Textual (Current) | TUIjoli (Target) | Improvement |
|--------|-------------------|------------------|-------------|
| **Startup Time** | 3-5 seconds | <100ms | **30-50x faster** |
| **Memory Usage** | ~50MB | ~15MB | **70% reduction** |
| **Bundle Size** | ~50MB (Python) | ~15MB (TypeScript) | **70% smaller** |
| **Rendering** | ~30fps | 60fps | **2x smoother** |

### Development Benefits

- ✅ **Modern patterns**: Functional components vs class-based widgets
- ✅ **Type safety**: Full TypeScript support with IDE autocomplete
- ✅ **Ecosystem**: Access to entire NPM package ecosystem
- ✅ **Testability**: Pure functions easier to test than stateful classes
- ✅ **Cross-platform**: Identical experience on all platforms

---

## Framework Choice: React vs Solid

### React (Recommended for Teams)

**Choose React if**:
- You have React experience on the team
- You need extensive third-party integrations
- Long-term maintenance by multiple developers
- You value ecosystem size over raw performance

**Pros**:
- Massive ecosystem (millions of packages)
- Familiar to most TypeScript developers
- Excellent tooling (DevTools, Testing Library)
- Vast community support

**Cons**:
- More boilerplate (`useCallback`, `useMemo`)
- Slightly slower re-renders (still 60fps for TUI)

---

### Solid (Recommended for Performance)

**Choose Solid if**:
- You're a solo developer or small team
- Performance is critical (10-100x faster re-renders)
- You want less boilerplate and simpler code
- Bundle size matters

**Pros**:
- **10-100x faster** re-renders (fine-grained reactivity)
- 50% smaller bundle than React
- Less boilerplate (no need for `useCallback`)
- Simpler mental model

**Cons**:
- Smaller ecosystem
- Less mature tooling
- Fewer developers familiar with it

---

## Migration Timeline (React)

### Phase 1: Setup (1 day)
- Initialize TypeScript project
- Port Python backend modules to TypeScript
- Create minimal "Hello World" TUI

### Phase 2: Simple Components (2-3 days)
- HelpTab (static text)
- StatusBar (3 reactive props)
- MetricsPanel (6 reactive props)
- ConfigTab (inputs, selects)

### Phase 3: Complex Components (3-5 days)
- SingleURLTab (11 state vars, async scraping)
- BatchTab (progress bar, table, async batch)
- MetricsTab (table, refresh, stats)

### Phase 4: Custom Components (2-3 days)
- CustomButton (clickable with hover)
- Checkbox (toggle state)
- ProgressBar (dynamic width)
- DataTable (scrollable grid)
- TabContainer (navigation)

### Phase 5: Integration (1-2 days)
- Wire all components together
- Implement tab navigation
- Add keyboard shortcuts

### Phase 6: Testing & Debugging (2-3 days)
- Component tests
- Integration tests
- Performance benchmarks
- Bug fixes

### Phase 7: Deployment (1 day)
- Build executable
- Update documentation
- Deploy to production

**Total**: 10-12 days

---

## Component Mapping (Quick Reference)

| Textual Python | TUIjoli TypeScript | Complexity |
|----------------|-------------------|-----------|
| `App` | `createCliRenderer()` + `createRoot()` | Medium |
| `StatusBar` (57 lines) | `StatusBar` (~40 lines) | **Low** |
| `MetricsPanel` (98 lines) | `MetricsPanel` (~50 lines) | **Low** |
| `HelpTab` (400 lines) | `HelpTab` (~30 lines) | **Low** |
| `ConfigTab` (350 lines) | `ConfigTab` (~100 lines) | **Medium** |
| `SingleURLTab` (200 lines) | `SingleURLTab` (~200 lines) | **High** |
| `BatchTab` (275 lines) | `BatchTab` (~250 lines) | **High** |
| `MetricsTab` (290 lines) | `MetricsTab` (~150 lines) | **Medium** |
| `ScrapouilleApp` (810 lines) | `App` (~300 lines) | **High** |

**Total Lines**: Python (1,680) → TypeScript (~1,120) = **33% reduction**

---

## Key Pattern Changes

### 1. State Management

**Textual**:
```python
class StatusBar(Static):
    status_text = reactive("Ready")  # Auto re-renders
```

**TUIjoli React**:
```tsx
function StatusBar() {
  const [statusText, setStatusText] = useState("Ready")  // Manual setters
  return <text content={statusText} />
}
```

**TUIjoli Solid**:
```tsx
function StatusBar() {
  const [statusText, setStatusText] = createSignal("Ready")  // Fine-grained
  return <text content={statusText()} />
}
```

---

### 2. Event Handling

**Textual**:
```python
def on_button_pressed(self, event: Button.Pressed) -> None:
    asyncio.create_task(self._async_handler())
```

**TUIjoli**:
```tsx
const handleClick = useCallback(async () => {
  setLoading(true)
  try {
    await asyncHandler()
  } finally {
    setLoading(false)
  }
}, [])

<CustomButton onClick={handleClick} />
```

---

### 3. Lifecycle Hooks

**Textual**:
```python
async def on_mount(self) -> None:
    self.cache = ScraperCache()
    await self.check_ollama_connection()
```

**TUIjoli React**:
```tsx
useEffect(() => {
  const init = async () => {
    const cache = new ScraperCache()
    await checkOllamaConnection()
  }
  init()
}, [])  // Empty deps = mount only
```

**TUIjoli Solid**:
```tsx
onMount(async () => {
  const cache = new ScraperCache()
  await checkOllamaConnection()
})
```

---

## Common Pitfalls to Avoid

### ❌ Pitfall 1: Forgetting State Setters
```tsx
// WRONG
const [count, setCount] = useState(0)
count += 1  // ❌ Doesn't trigger re-render

// CORRECT
setCount(count + 1)  // ✅ Triggers re-render
```

---

### ❌ Pitfall 2: Direct Child Manipulation
```tsx
// WRONG (Textual pattern)
panelRef.current.executionTime = 5.2  // ❌ Anti-pattern

// CORRECT (React/Solid pattern)
const [executionTime, setExecutionTime] = useState(0)
setExecutionTime(5.2)  // ✅ Props-based communication
```

---

### ❌ Pitfall 3: CSS to Inline Styles
```python
# Textual CSS
CSS = """
.results-container {
    width: 2fr;
    height: 20;
    border: solid $primary;
}
"""
```

```tsx
// TUIjoli inline styles
<box style={{
  width: "2fr",
  height: 20,
  border: true,
  borderColor: "#3b82f6"
}}>
```

---

## Testing Strategy

### Unit Tests (Component-Level)
- Framework: Vitest + Testing Library
- Test each component in isolation
- Verify props, state, event handlers

### Integration Tests (Flow-Level)
- Framework: Vitest + Mock Backend
- Test complete user workflows
- Verify single URL scraping, batch processing, metrics

### Performance Benchmarks
- Startup time: Target <100ms
- Memory usage: Target <15MB
- Rendering: Target 60fps

**Example Test**:
```tsx
import { describe, it, expect } from "vitest"
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

## Risk Mitigation

### Low Risk
- ✅ Simple components (StatusBar, HelpTab)
- ✅ Backend module ports (straightforward Python → TypeScript)
- ✅ Testing infrastructure (mature tooling)

### Medium Risk
- ⚠️ Custom components (Button, Table) - Need careful design
- ⚠️ Async operations - Different patterns than Python
- ⚠️ Tab navigation - May need custom implementation

### High Risk
- 🚨 Complex workflows (batch processing) - Most intricate logic
- 🚨 DataTable component - No built-in equivalent in TUIjoli
- 🚨 Feature parity - Must maintain all 175+ features

**Mitigation**:
1. **Incremental migration**: Start with simple components, build confidence
2. **Parallel development**: Keep Python version running during migration
3. **Test coverage**: 80%+ coverage before deprecating Python version
4. **Feature flagging**: Allow users to choose Python or TypeScript TUI

---

## Success Metrics

### Must-Have (Launch Blockers)
- ✅ Feature parity: All 175+ unit tests pass
- ✅ Performance: <100ms startup, <15MB memory
- ✅ Stability: No crashes for 1 hour of continuous use
- ✅ Documentation: Updated README, CLAUDE.md

### Nice-to-Have (Post-Launch)
- 🎯 Code quality: <5% code duplication
- 🎯 Test coverage: >80% line coverage
- 🎯 Bundle size: <10MB (stretch goal)
- 🎯 Accessibility: Keyboard-only navigation

---

## Decision Matrix

| Factor | Weight | React Score | Solid Score | Notes |
|--------|--------|-------------|-------------|-------|
| **Performance** | 25% | 7/10 | 10/10 | Solid 10-100x faster re-renders |
| **Ecosystem** | 20% | 10/10 | 6/10 | React has massive ecosystem |
| **Learning Curve** | 15% | 7/10 | 8/10 | Solid simpler, but less familiar |
| **Tooling** | 15% | 9/10 | 7/10 | React DevTools superior |
| **Bundle Size** | 10% | 7/10 | 9/10 | Solid 50% smaller |
| **Community** | 10% | 10/10 | 6/10 | React has 100x more developers |
| **Type Safety** | 5% | 9/10 | 9/10 | Both excellent TypeScript support |
| **Total** | 100% | **8.15/10** | **8.05/10** | **Very close!** |

**Recommendation**: **React** for teams/long-term projects, **Solid** for solo/performance-critical

---

## Next Steps

1. **Choose framework**: React (ecosystem) or Solid (performance)
2. **Read full guide**: `TEXTUAL-TO-TUIJOLI-MIGRATION-GUIDE.md` (86 pages)
3. **Setup project**: `mkdir tui-ts && cd tui-ts && bun init`
4. **Install deps**: `bun add @opentui/core @opentui/react react`
5. **Start Phase 1**: Setup TypeScript project (1 day)
6. **Iterate**: Follow phases 2-7 (10-12 days total)
7. **Test**: Ensure feature parity
8. **Deploy**: Build executable, update docs

---

## Resources

- **Full Migration Guide**: `TEXTUAL-TO-TUIJOLI-MIGRATION-GUIDE.md` (86 pages, 9,000+ lines)
- **TUIjoli Docs**: https://github.com/BasicFist/TUIjoli
- **TUIjoli React**: https://github.com/BasicFist/TUIjoli/tree/main/packages/react
- **TUIjoli Solid**: https://github.com/BasicFist/TUIjoli/tree/main/packages/solid
- **React Docs**: https://react.dev
- **Solid Docs**: https://solidjs.com
- **Scrapouille Context**: `CLAUDE.md` (project-specific)

---

**Questions?** Refer to Section 6 (Common Pitfalls) and Section 8 (FAQ) in the full guide.

**Ready to Start?** Follow Section 4 (Refactoring Steps) for the detailed 7-phase plan! 🚀
