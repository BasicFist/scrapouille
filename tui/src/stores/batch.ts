/**
 * Batch Processing State Management (SolidJS Signals)
 * Manages batch scraping operations with multiple URLs
 */

import { createSignal } from 'solid-js'
import type { BatchScrapeResponse, BatchResult } from '../api/types'

// === Batch Form State ===

export const [batchUrls, setBatchUrls] = createSignal<string>('')
export const [batchPrompt, setBatchPrompt] = createSignal<string>('')
export const [batchModel, setBatchModel] = createSignal<string>('qwen2.5-coder:7b')
export const [batchSchema, setBatchSchema] = createSignal<string | null>(null)
export const [batchMaxConcurrent, setBatchMaxConcurrent] = createSignal<number>(5)
export const [batchTimeoutPerUrl, setBatchTimeoutPerUrl] = createSignal<number>(30)
export const [batchUseCache, setBatchUseCache] = createSignal<boolean>(true)
export const [batchUseRateLimiting, setBatchUseRateLimiting] = createSignal<boolean>(true)
export const [batchUseStealth, setBatchUseStealth] = createSignal<boolean>(false)

// === Batch Execution State ===

export const [isBatchProcessing, setIsBatchProcessing] = createSignal<boolean>(false)
export const [batchProgress, setBatchProgress] = createSignal<number>(0)
export const [batchTotal, setBatchTotal] = createSignal<number>(0)
export const [batchResult, setBatchResult] = createSignal<BatchScrapeResponse | null>(null)
export const [batchError, setBatchError] = createSignal<string | null>(null)

// === Derived State ===

export const parsedUrls = () => {
  return batchUrls()
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
}

export const urlCount = () => parsedUrls().length

export const canProcessBatch = () => {
  return (
    !isBatchProcessing() &&
    urlCount() > 0 &&
    urlCount() <= 100 &&
    batchPrompt().trim().length >= 5
  )
}

export const progressPercentage = () => {
  if (batchTotal() === 0) return 0
  return Math.round((batchProgress() / batchTotal()) * 100)
}

export const hasResults = () => batchResult() !== null

// === Actions ===

export function clearBatchResults() {
  setBatchResult(null)
  setBatchError(null)
  setBatchProgress(0)
  setBatchTotal(0)
}

export function resetBatchForm() {
  setBatchUrls('')
  setBatchPrompt('')
  setBatchSchema(null)
  clearBatchResults()
}

export function updateProgress(done: number, total: number) {
  setBatchProgress(done)
  setBatchTotal(total)
}

// === File Upload Helpers ===

export async function loadUrlsFromFile(file: File): Promise<void> {
  const text = await file.text()

  // Handle CSV format (extract URLs from first column)
  if (file.name.endsWith('.csv')) {
    const lines = text.split('\n')
    const urls = lines
      .map(line => {
        // Get first column (split by comma)
        const firstCol = line.split(',')[0].trim()
        // Remove quotes if present
        return firstCol.replace(/^["']|["']$/g, '')
      })
      .filter(url => url.startsWith('http'))

    setBatchUrls(urls.join('\n'))
  } else {
    // Plain text - one URL per line
    const urls = text
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.startsWith('http'))

    setBatchUrls(urls.join('\n'))
  }
}
