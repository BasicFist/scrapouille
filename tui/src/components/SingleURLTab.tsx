/**
 * Single URL Tab Component
 * Form for scraping a single URL with prompt
 */

import { Show, createEffect } from 'solid-js'
import { Input } from './widgets/Input'
import { TextArea } from './widgets/TextArea'
import { Select } from './widgets/Select'
import { Checkbox } from './widgets/Checkbox'
import { Button } from './widgets/Button'
import { apiClient } from '../api/client'
import type { ScrapeRequest } from '../api/types'
import {
  scrapingUrl,
  setScrapingUrl,
  scrapingPrompt,
  setScrapingPrompt,
  scrapingModel,
  setScrapingModel,
  scrapingSchema,
  setScrapingSchema,
  scrapingRateLimit,
  setScrapingRateLimit,
  scrapingStealthLevel,
  setScrapingStealthLevel,
  scrapingUseCache,
  setScrapingUseCache,
  scrapingMarkdownMode,
  setScrapingMarkdownMode,
  isScraping,
  setIsScraping,
  scrapeResult,
  setScrapeResult,
  scrapeError,
  setScrapeError,
  canScrape,
  clearScrapeResults,
  resetScrapeForm,
} from '../stores/scraper'

const MODELS = [
  'qwen2.5-coder:7b',
  'llama3.1',
  'deepseek-coder-v2',
  'codellama',
]

const SCHEMAS = ['none', 'product', 'article', 'job', 'research', 'contact']

const RATE_LIMIT_MODES = ['aggressive', 'normal', 'polite', 'none']

const STEALTH_LEVELS = ['off', 'low', 'medium', 'high']

export function SingleURLTab() {
  const handleScrape = async () => {
    if (!canScrape()) return

    setIsScraping(true)
    setScrapeError(null)
    setScrapeResult(null)

    try {
      const request: ScrapeRequest = {
        url: scrapingUrl(),
        prompt: scrapingPrompt(),
        model: scrapingModel(),
        schema_name: scrapingSchema() === 'none' ? null : scrapingSchema(),
        rate_limit_mode: scrapingRateLimit(),
        stealth_level: scrapingStealthLevel(),
        use_cache: scrapingUseCache(),
        markdown_mode: scrapingMarkdownMode(),
      }

      const result = await apiClient.scrapeSingleURL(request)
      setScrapeResult(result)

      if (!result.success) {
        setScrapeError(result.error || 'Unknown error')
      }
    } catch (error: any) {
      setScrapeError(error.message || 'Failed to scrape URL')
      setScrapeResult(null)
    } finally {
      setIsScraping(false)
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
          Single URL Scraping
        </text>
        <Button
          label="Reset Form"
          onclick={resetScrapeForm}
          variant="secondary"
          disabled={isScraping()}
        />
      </box>

      {/* Main content area - scrollable */}
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
            <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
              Target URL *
            </text>
            <Input
              value={scrapingUrl()}
              onchange={setScrapingUrl}
              placeholder="https://example.com"
              disabled={isScraping()}
              width="100%"
            />
          </box>

          {/* Prompt Input */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
              Extraction Prompt *
            </text>
            <TextArea
              value={scrapingPrompt()}
              onchange={setScrapingPrompt}
              placeholder="Extract product name, price, and description..."
              height={4}
              width="100%"
              disabled={isScraping()}
            />
            <text style={{ color: '#6E7681', fontSize: 10 }}>
              Minimum 5 characters
            </text>
          </box>

          {/* Model Selection */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>Model</text>
            <Select
              value={scrapingModel()}
              options={MODELS}
              onchange={setScrapingModel}
              disabled={isScraping()}
              width="100%"
            />
          </box>

          {/* Schema Selection */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
              Validation Schema
            </text>
            <Select
              value={scrapingSchema() || 'none'}
              options={SCHEMAS}
              onchange={(val) => setScrapingSchema(val === 'none' ? null : val)}
              disabled={isScraping()}
              width="100%"
            />
          </box>

          {/* Options Row */}
          <box
            style={{
              flexDirection: 'row',
              gap: 2,
              flexWrap: 'wrap',
            }}
          >
            {/* Rate Limiting */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Rate Limit
              </text>
              <Select
                value={scrapingRateLimit()}
                options={RATE_LIMIT_MODES}
                onchange={setScrapingRateLimit}
                disabled={isScraping()}
                width="100%"
              />
            </box>

            {/* Stealth Level */}
            <box style={{ flexDirection: 'column', gap: 0.5, flex: 1 }}>
              <text style={{ color: '#E6EDF3', fontWeight: 'bold' }}>
                Stealth Level
              </text>
              <Select
                value={scrapingStealthLevel()}
                options={STEALTH_LEVELS}
                onchange={setScrapingStealthLevel}
                disabled={isScraping()}
                width="100%"
              />
            </box>
          </box>

          {/* Checkboxes */}
          <box style={{ flexDirection: 'column', gap: 0.5 }}>
            <Checkbox
              checked={scrapingUseCache()}
              onchange={setScrapingUseCache}
              label="Use cache (faster for repeated requests)"
              disabled={isScraping()}
            />
            <Checkbox
              checked={scrapingMarkdownMode()}
              onchange={setScrapingMarkdownMode}
              label="Markdown mode (no AI processing)"
              disabled={isScraping()}
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
              label={isScraping() ? 'Scraping...' : 'Scrape URL'}
              onclick={handleScrape}
              disabled={!canScrape()}
              variant="primary"
              width="60%"
            />
            <Button
              label="Clear Results"
              onclick={clearScrapeResults}
              disabled={isScraping() || !scrapeResult()}
              variant="secondary"
              width="40%"
            />
          </box>
        </box>

        {/* Right Panel - Results */}
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
            Results
          </text>

          <Show
            when={scrapeResult()}
            fallback={
              <box
                style={{
                  flex: 1,
                  justifyContent: 'center',
                  alignItems: 'center',
                }}
              >
                <text style={{ color: '#6E7681' }}>
                  {isScraping()
                    ? 'Scraping in progress...'
                    : 'No results yet. Fill in the form and click "Scrape URL".'}
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
                    {result().success ? '✓ Success' : '✗ Failed'}
                  </text>
                </box>

                {/* Metadata Panel */}
                <box
                  style={{
                    padding: 1,
                    backgroundColor: '#161B22',
                    border: '1px solid #30363D',
                    flexDirection: 'column',
                    gap: 0.5,
                  }}
                >
                  <text style={{ color: '#4ECDC4', fontWeight: 'bold' }}>
                    Metadata
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Model: {result().metadata.model_used}
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Time: {result().metadata.execution_time.toFixed(2)}s
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Fallback Attempts: {result().metadata.fallback_attempts}
                  </text>
                  <text style={{ color: '#E6EDF3' }}>
                    Cached: {result().metadata.cached ? 'Yes' : 'No'}
                  </text>
                  <Show when={result().metadata.validation_passed !== null}>
                    <text style={{ color: '#E6EDF3' }}>
                      Validation:{' '}
                      {result().metadata.validation_passed ? 'Passed' : 'Failed'}
                    </text>
                  </Show>
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

                {/* Extracted Data */}
                <Show when={result().success && result().data}>
                  <box
                    style={{
                      padding: 1,
                      backgroundColor: '#161B22',
                      border: '1px solid #30363D',
                      flexDirection: 'column',
                      gap: 0.5,
                      maxHeight: 20,
                      overflow: 'auto',
                    }}
                  >
                    <text style={{ color: '#4ECDC4', fontWeight: 'bold' }}>
                      Extracted Data
                    </text>
                    <text style={{ color: '#E6EDF3', fontFamily: 'monospace' }}>
                      {JSON.stringify(result().data, null, 2)}
                    </text>
                  </box>
                </Show>
              </box>
            )}
          </Show>
        </box>
      </box>
    </box>
  )
}
