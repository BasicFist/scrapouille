/**
 * Scraper State Management (SolidJS Signals)
 * Manages scraping operations and results
 */

import { createSignal } from 'solid-js'
import type { ScrapeResponse } from '../api/types'

// === Single URL Scraping State ===

export const [scrapingUrl, setScrapingUrl] = createSignal<string>('')
export const [scrapingPrompt, setScrapingPrompt] = createSignal<string>('')
export const [scrapingModel, setScrapingModel] = createSignal<string>('qwen2.5-coder:7b')
export const [scrapingSchema, setScrapingSchema] = createSignal<string | null>(null)
export const [scrapingRateLimit, setScrapingRateLimit] = createSignal<string>('normal')
export const [scrapingStealthLevel, setScrapingStealthLevel] = createSignal<string>('off')
export const [scrapingUseCache, setScrapingUseCache] = createSignal<boolean>(true)
export const [scrapingMarkdownMode, setScrapingMarkdownMode] = createSignal<boolean>(false)

// === Scraping Execution State ===

export const [isScraping, setIsScraping] = createSignal<boolean>(false)
export const [scrapeResult, setScrapeResult] = createSignal<ScrapeResponse | null>(null)
export const [scrapeError, setScrapeError] = createSignal<string | null>(null)

// === Derived State ===

export const canScrape = () => {
  return (
    !isScraping() &&
    scrapingUrl().trim().length > 0 &&
    scrapingPrompt().trim().length >= 5
  )
}

export const hasResult = () => scrapeResult() !== null

// === Actions ===

export function clearScrapeResults() {
  setScrapeResult(null)
  setScrapeError(null)
}

export function resetScrapeForm() {
  setScrapingUrl('')
  setScrapingPrompt('')
  setScrapingSchema(null)
  clearScrapeResults()
}
