/**
 * Batch Processing Tab Component
 * Form for scraping multiple URLs concurrently
 */

import { Show, createEffect } from 'solid-js'
import { TextArea } from './widgets/TextArea'
import { Select } from './widgets/Select'
import { Button } from './widgets/Button'
import { Checkbox } from './widgets/Checkbox'
import { apiClient } from '../api/client'
import type { BatchScrapeRequest } from '../api/types'
import {
  batchUrls,
  setBatchUrls,
  batchPrompt,
  setBatchPrompt,
  batchModel,
  setBatchModel,
  batchSchema,
  setBatchSchema,
  batchMaxConcurrent,
  setBatchMaxConcurrent,
  batchTimeoutPerUrl,
  setBatchTimeoutPerUrl,
  batchUseCache,
  setBatchUseCache,
  batchUseRateLimiting,
  setBatchUseRateLimiting,
  batchUseStealth,
  setBatchUseStealth,
  isBatchProcessing,
  setIsBatchProcessing,
  batchProgress,
  batchTotal,
  batchResult,
  setBatchResult,
  batchError,
  setBatchError,
  parsedUrls,
  urlCount,
  canProcessBatch,
  progressPercentage,
  clearBatchResults,
  resetBatchForm,
  updateProgress,
  loadUrlsFromFile,
} from '../stores/batch'

const MODELS = [
  'qwen2.5-coder:7b',
  'llama3.1',
  'deepseek-coder-v2',
  'codellama',
]

const SCHEMAS = ['none', 'product', 'article', 'job', 'research', 'contact']

const CONCURRENCY_OPTIONS = [
  { label: '1 (Sequential)', value: '1' },
  { label: '3 (Slow)', value: '3' },
  { label: '5 (Normal)', value: '5' },
  { label: '10 (Fast)', value: '10' },
  { label: '20 (Maximum)', value: '20' },
]

const TIMEOUT_OPTIONS = [
  { label: '10s (Quick)', value: '10' },
  { label: '30s (Normal)', value: '30' },
  { label: '60s (Patient)', value: '60' },
  { label: '120s (Maximum)', value: '120' },
]

export function BatchProcessingTab() {
  const handleFileUpload = async (event: any) => {
    const file = event.target.files?.[0]
    if (file) {
      try {
        await loadUrlsFromFile(file)
      } catch (error: any) {
        setBatchError(`Failed to load file: ${error.message}`)
      }
    }
  }

  const handleBatchScrape = async () => {
    if (!canProcessBatch()) return

    setIsBatchProcessing(true)
    setBatchError(null)
    setBatchResult(null)

    const urls = parsedUrls()
    updateProgress(0, urls.length)

    try {
      const request: BatchScrapeRequest = {
        urls: urls,
        prompt: batchPrompt(),
        model: batchModel(),
        schema_name: batchSchema() === 'none' ? null : batchSchema(),
        max_concurrent: batchMaxConcurrent(),
        timeout_per_url: batchTimeoutPerUrl(),
        use_cache: batchUseCache(),
        use_rate_limiting: batchUseRateLimiting(),
        use_stealth: batchUseStealth(),
      }

      // Note: Progress updates would require WebSocket/SSE for real-time updates
      // For now, we just show indeterminate progress until completion
      const result = await apiClient.scrapeBatch(request)
      setBatchResult(result)

      if (!result.success) {
        setBatchError(result.error || 'Batch processing failed')
      }
    } catch (error: any) {
      setBatchError(error.message || 'Failed to process batch')
      setBatchResult(null)
    } finally {
      setIsBatchProcessing(false)
    }
  }

  return (
    <box
      style={{
        width: '100%',
        height: '100%',
        flexDirection: 'column',
        padding: 1,
        gap: 1,
      }}
    >
      {/* Header */}
      <box
        style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #30363D',
          paddingBottom: 1,
        }}
      >
        <text
          style={{
            color: '#4ECDC4',
            fontWeight: 'bold',
            fontSize: 16,
          }}
        >
          Batch Processing
        </text>
        <Button
          label="Reset Form"
          onclick={resetBatchForm}
          variant="secondary"
          disabled={isBatchProcessing()}
        />
      </box>

      {/* Main content area */}
      <box
        style={{
          flex: 1,
          flexDirection: 'row',
          gap: 2,
          overflow: 'auto',
        }}
      >
        {/* Left Panel - Form */}
        <box
          style={{
            width: '50%',
            flexDirection: 'column',
            gap: 1,
          }}
        >
          {/* URL Input */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <box
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                URLs * ({urlCount()}/100)
              </text>
              <input
                type="file"
                accept=".txt,.csv"
                onchange={handleFileUpload}
                disabled={isBatchProcessing()}
                style={{
                  color: '#E6EDF3',
                  fontSize: 10,
                }}
              />
            </box>
            <TextArea
              value={batchUrls()}
              onchange={setBatchUrls}
              placeholder="Enter URLs (one per line) or upload CSV/TXT file"
              height={8}
              width="100%"
              disabled={isBatchProcessing()}
            />
            <text style={{ color: '#6E7681', fontSize: 10 }}>
              1-100 URLs, one per line
            </text>
          </box>

          {/* Prompt Input */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
              Shared Extraction Prompt *
            </text>
            <TextArea
              value={batchPrompt()}
              onchange={setBatchPrompt}
              placeholder="Extract product name, price, and description..."
              height={4}
              width="100%"
              disabled={isBatchProcessing()}
            />
            <text style={{ color: '#6E7681', fontSize: 10 }}>
              This prompt will be used for all URLs
            </text>
          </box>

          {/* Configuration Row 1 */}
          <box
            style={{
              flexDirection: 'row',
              gap: 2,
            }}
          >
            {/* Model */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Model
              </text>
              <Select
                value={batchModel()}
                options={MODELS}
                onchange={setBatchModel}
                disabled={isBatchProcessing()}
                width="100%"
              />
            </box>

            {/* Schema */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Schema
              </text>
              <Select
                value={batchSchema() || 'none'}
                options={SCHEMAS}
                onchange={(val) => setBatchSchema(val === 'none' ? null : val)}
                disabled={isBatchProcessing()}
                width="100%"
              />
            </box>
          </box>

          {/* Configuration Row 2 */}
          <box
            style={{
              flexDirection: 'row',
              gap: 2,
            }}
          >
            {/* Concurrency */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Concurrency
              </text>
              <Select
                value={String(batchMaxConcurrent())}
                options={CONCURRENCY_OPTIONS}
                onchange={(val) => setBatchMaxConcurrent(parseInt(val))}
                disabled={isBatchProcessing()}
                width="100%"
              />
            </box>

            {/* Timeout */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Timeout/URL
              </text>
              <Select
                value={String(batchTimeoutPerUrl())}
                options={TIMEOUT_OPTIONS}
                onchange={(val) => setBatchTimeoutPerUrl(parseInt(val))}
                disabled={isBatchProcessing()}
                width="100%"
              />
            </box>
          </box>

          {/* Checkboxes */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <Checkbox
              checked={batchUseCache()}
              onchange={setBatchUseCache}
              label="Use cache (faster for repeated URLs)"
              disabled={isBatchProcessing()}
            />
            <Checkbox
              checked={batchUseRateLimiting()}
              onchange={setBatchUseRateLimiting}
              label="Rate limiting (polite scraping)"
              disabled={isBatchProcessing()}
            />
            <Checkbox
              checked={batchUseStealth()}
              onchange={setBatchUseStealth}
              label="Stealth mode (anti-detection)"
              disabled={isBatchProcessing()}
            />
          </box>

          {/* Action Buttons */}
          <box
            style={{
              flexDirection: 'row',
              gap: 1,
              marginTop: 1,
            }}
          >
            <Button
              label={
                isBatchProcessing()
                  ? `Processing... (${progressPercentage()}%)`
                  : 'Start Batch'
              }
              onclick={handleBatchScrape}
              disabled={!canProcessBatch()}
              variant="primary"
              width="60%"
            />
            <Button
              label="Clear Results"
              onclick={clearBatchResults}
              disabled={isBatchProcessing() || !batchResult()}
              variant="secondary"
              width="40%"
            />
          </box>

          {/* Progress Bar */}
          <Show when={isBatchProcessing()}>
            <box
              style={{
                padding: 1,
                backgroundColor: '#161B22',
                border: '1px solid #30363D',
                borderRadius: 4,
                flexDirection: 'column',
                gap: 0.5,
              }}
            >
              <text style={{ color: '#E6EDF3' }}>
                Processing: {batchProgress()} / {batchTotal()} URLs
              </text>
              <box
                style={{
                  width: '100%',
                  height: 1,
                  backgroundColor: '#30363D',
                  borderRadius: 2,
                }}
              >
                <box
                  style={{
                    width: `${progressPercentage()}%`,
                    height: '100%',
                    backgroundColor: '#4ECDC4',
                    borderRadius: 2,
                  }}
                />
              </box>
            </box>
          </Show>
        </box>

        {/* Right Panel - Results Summary */}
        <box
          style={{
            width: '50%',
            flexDirection: 'column',
            gap: 1,
            borderLeft: '1px solid #30363D',
            paddingLeft: 2,
          }}
        >
          <text style={{ color: '#E6EDF3', fontWeight: 'bold', fontSize: 14 }}>
            Results Summary
          </text>

          <Show
            when={batchResult()}
            fallback={
              <box
                style={{
                  flex: 1,
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <text style={{ color: '#6E7681' }}>
                  {isBatchProcessing()
                    ? 'Processing batch...'
                    : 'No results yet. Configure and start batch processing.'}
                </text>
              </box>
            }
          >
            {(result) => (
              <box style={{ flexDirection: 'column', gap: 1 }}>
                {/* Status Banner */}
                <box
                  style={{
                    padding: 1,
                    backgroundColor: result().success ? '#1F6E3E' : '#6E1F1F',
                    borderRadius: 4,
                  }}
                >
                  <text
                    style={{
                      color: '#E6EDF3',
                      fontWeight: 'bold',
                    }}
                  >
                    {result().success
                      ? `✓ Batch Complete (${result().summary.successful}/${result().summary.total} succeeded)`
                      : '✗ Batch Failed'}
                  </text>
                </box>

                {/* Summary Statistics */}
                <box
                  style={{
                    flexDirection: 'row',
                    gap: 1,
                    flexWrap: 'wrap',
                  }}
                >
                  {/* Total */}
                  <box
                    style={{
                      flex: 1,
                      minWidth: 15,
                      padding: 1,
                      backgroundColor: '#161B22',
                      border: '1px solid #30363D',
                      borderRadius: 4,
                      flexDirection: 'column',
                      gap: 0.3,
                    }}
                  >
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Total
                    </text>
                    <text
                      style={{
                        color: '#4ECDC4',
                        fontSize: 18,
                        fontWeight: 'bold',
                      }}
                    >
                      {result().summary.total}
                    </text>
                  </box>

                  {/* Successful */}
                  <box
                    style={{
                      flex: 1,
                      minWidth: 15,
                      padding: 1,
                      backgroundColor: '#161B22',
                      border: '1px solid #30363D',
                      borderRadius: 4,
                      flexDirection: 'column',
                      gap: 0.3,
                    }}
                  >
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Success
                    </text>
                    <text
                      style={{
                        color: '#3FB950',
                        fontSize: 18,
                        fontWeight: 'bold',
                      }}
                    >
                      {result().summary.successful}
                    </text>
                  </box>

                  {/* Failed */}
                  <box
                    style={{
                      flex: 1,
                      minWidth: 15,
                      padding: 1,
                      backgroundColor: '#161B22',
                      border: '1px solid #30363D',
                      borderRadius: 4,
                      flexDirection: 'column',
                      gap: 0.3,
                    }}
                  >
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Failed
                    </text>
                    <text
                      style={{
                        color: '#FF7B72',
                        fontSize: 18,
                        fontWeight: 'bold',
                      }}
                    >
                      {result().summary.failed}
                    </text>
                  </box>

                  {/* Cached */}
                  <box
                    style={{
                      flex: 1,
                      minWidth: 15,
                      padding: 1,
                      backgroundColor: '#161B22',
                      border: '1px solid #30363D',
                      borderRadius: 4,
                      flexDirection: 'column',
                      gap: 0.3,
                    }}
                  >
                    <text style={{ color: '#6E7681', fontSize: 10 }}>
                      Cached
                    </text>
                    <text
                      style={{
                        color: '#4ECDC4',
                        fontSize: 18,
                        fontWeight: 'bold',
                      }}
                    >
                      {result().summary.cached}
                    </text>
                  </box>
                </box>

                {/* Timing Statistics */}
                <box
                  style={{
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    borderRadius: 4,
                    flexDirection: 'column',
                    gap: 0.5,
                  }}
                >
                  <text style={{ color: '#4ECDC4', fontWeight: 'bold' }}>
                    Timing
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Total Time: {result().summary.total_time}s
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Avg Per URL: {result().summary.avg_time_per_url}s
                  </text>
                </box>

                {/* Error Message */}
                <Show when={!result().success && result().error}>
                  <box
                    style={{
                      padding: 1,
                      backgroundColor: '#2D1B1B',
                      border: '1px solid #6E1F1F',
                      borderRadius: 4,
                    }}
                  >
                    <text style={{ color: '#FF7B72' }}>
                      Error: {result().error}
                    </text>
                  </box>
                </Show>

                {/* View Results Button */}
                <Button
                  label="View Detailed Results Table →"
                  onclick={() => {
                    // TODO: Navigate to results table or show modal
                    console.log('Navigate to results table')
                  }}
                  variant="primary"
                  width="100%"
                />

                {/* Export Options */}
                <box style={{ flexDirection: 'row', gap: 1 }}>
                  <Button
                    label="Export CSV"
                    onclick={() => {
                      // TODO: Export to CSV
                      console.log('Export CSV')
                    }}
                    variant="secondary"
                    width="50%"
                  />
                  <Button
                    label="Export JSON"
                    onclick={() => {
                      // TODO: Export to JSON
                      console.log('Export JSON')
                    }}
                    variant="secondary"
                    width="50%"
                  />
                </box>
              </box>
            )}
          </Show>
        </box>
      </box>
    </box>
  )
}
