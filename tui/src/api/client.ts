/**
 * HTTP Client for Scrapouille Backend API
 * Handles all communication with FastAPI server
 */

import type {
  HealthResponse,
  APIError,
  ScrapeRequest,
  ScrapeResponse,
  BatchScrapeRequest,
  BatchScrapeResponse,
  MetricsStats,
  MetricsStatsResponse,
  MetricsRecentResponse,
} from './types'

export class ScrapouilleAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public context?: Record<string, any>
  ) {
    super(message)
    this.name = 'ScrapouilleAPIError'
  }
}

export class ScrapouilleAPIClient {
  private baseURL: string
  private timeout: number

  constructor(baseURL: string = 'http://localhost:8000', timeout: number = 30000) {
    this.baseURL = baseURL
    this.timeout = timeout
  }

  /**
   * Check API health and backend connections
   * Used by status bar to show connection indicators
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        signal: AbortSignal.timeout(5000), // 5s timeout for health check
      })

      if (!response.ok) {
        throw new ScrapouilleAPIError(
          `Health check failed: ${response.statusText}`,
          response.status
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ScrapouilleAPIError) {
        throw error
      }

      // Network error (API server not running)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new ScrapouilleAPIError(
          'API server not running. Start with: ./run-api.sh',
          0,
          'ECONNREFUSED'
        )
      }

      // Timeout error
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ScrapouilleAPIError(
          'Health check timeout',
          0,
          'ETIMEDOUT'
        )
      }

      throw new ScrapouilleAPIError(
        `Unexpected error: ${error instanceof Error ? error.message : String(error)}`,
        0
      )
    }
  }

  /**
   * Test API connectivity with a simple ping
   * Returns true if API is reachable, false otherwise
   */
  async ping(): Promise<boolean> {
    try {
      await this.checkHealth()
      return true
    } catch {
      return false
    }
  }

  // === Scraping Endpoints (Phase 2) ===

  /**
   * Scrape a single URL with the given prompt and options
   */
  async scrapeSingleURL(request: ScrapeRequest): Promise<ScrapeResponse> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: AbortSignal.timeout(this.timeout),
      })

      if (!response.ok) {
        const errorData: APIError = await response.json()
        throw new ScrapouilleAPIError(
          errorData.detail || `Scrape failed: ${response.statusText}`,
          response.status,
          errorData.code,
          errorData.context
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ScrapouilleAPIError) {
        throw error
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ScrapouilleAPIError(
          'Scrape request timeout',
          0,
          'ETIMEDOUT'
        )
      }

      throw new ScrapouilleAPIError(
        `Scrape failed: ${error instanceof Error ? error.message : String(error)}`,
        0
      )
    }
  }

  /**
   * Scrape multiple URLs concurrently with progress tracking
   */
  async scrapeBatch(request: BatchScrapeRequest): Promise<BatchScrapeResponse> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/scrape/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: AbortSignal.timeout(this.timeout * 10), // 5 minutes for batch
      })

      if (!response.ok) {
        const errorData: APIError = await response.json()
        throw new ScrapouilleAPIError(
          errorData.detail || `Batch scrape failed: ${response.statusText}`,
          response.status,
          errorData.code,
          errorData.context
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ScrapouilleAPIError) {
        throw error
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ScrapouilleAPIError(
          'Batch scrape request timeout',
          0,
          'ETIMEDOUT'
        )
      }

      throw new ScrapouilleAPIError(
        `Batch scrape failed: ${error instanceof Error ? error.message : String(error)}`,
        0
      )
    }
  }

  // === Metrics Endpoints (Phase 4) ===

  /**
   * Get combined metrics statistics (7-day stats + recent scrapes)
   */
  async getMetricsStats(): Promise<MetricsStats> {
    try {
      // Fetch both stats and recent scrapes in parallel
      const [statsResponse, recentResponse] = await Promise.all([
        fetch(`${this.baseURL}/api/v1/metrics/stats`, {
          signal: AbortSignal.timeout(5000),
        }),
        fetch(`${this.baseURL}/api/v1/metrics/recent?limit=10`, {
          signal: AbortSignal.timeout(5000),
        }),
      ])

      if (!statsResponse.ok) {
        throw new ScrapouilleAPIError(
          `Failed to fetch metrics: ${statsResponse.statusText}`,
          statsResponse.status
        )
      }

      if (!recentResponse.ok) {
        throw new ScrapouilleAPIError(
          `Failed to fetch recent scrapes: ${recentResponse.statusText}`,
          recentResponse.status
        )
      }

      const stats: MetricsStatsResponse = await statsResponse.json()
      const recent: MetricsRecentResponse = await recentResponse.json()

      // Combine into single MetricsStats object
      return {
        total_scrapes: stats.total_scrapes,
        avg_execution_time: stats.avg_time,
        cache_hit_rate: stats.cache_hit_rate,
        error_rate: stats.error_rate,
        model_usage: stats.model_usage,
        recent_scrapes: recent.scrapes,
      }
    } catch (error) {
      if (error instanceof ScrapouilleAPIError) {
        throw error
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ScrapouilleAPIError(
          'Metrics request timeout',
          0,
          'ETIMEDOUT'
        )
      }

      throw new ScrapouilleAPIError(
        `Failed to load metrics: ${error instanceof Error ? error.message : String(error)}`,
        0
      )
    }
  }

  // === Config Endpoints (Phase 4) ===
  // TODO: Implement getConfig, updateConfig, etc.
}

/**
 * Default API client instance
 */
export const apiClient = new ScrapouilleAPIClient()
