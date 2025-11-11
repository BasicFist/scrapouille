/**
 * TypeScript types for Scrapouille API
 * Mirrors Python Pydantic models from FastAPI backend
 */

// === Health Check ===

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy"
  timestamp: string
  uptime_seconds: number
  version: string
  connections: {
    ollama: boolean
    redis: boolean
  }
  backend: {
    cache_enabled: boolean
    metrics_enabled: boolean
  }
}

// === API Error ===

export interface APIError {
  detail: string
  code?: string
  context?: Record<string, any>
}

// === Scraping (Phase 2) ===

export interface ScrapeRequest {
  url: string
  prompt: string
  model?: string
  schema_name?: string | null
  rate_limit_mode?: "none" | "aggressive" | "normal" | "polite"
  stealth_level?: "off" | "low" | "medium" | "high"
  use_cache?: boolean
  markdown_mode?: boolean
}

export interface ScrapeResponse {
  success: boolean
  data: Record<string, any> | null
  metadata: {
    execution_time: number
    model_used: string
    fallback_attempts: number
    cached: boolean
    validation_passed: boolean | null
  }
  error?: string
}

// === Batch Processing (Phase 3) ===

export interface BatchScrapeRequest {
  urls: string[]
  prompt: string
  model?: string
  schema_name?: string | null
  max_concurrent?: number
  timeout_per_url?: number
  use_cache?: boolean
  use_rate_limiting?: boolean
  use_stealth?: boolean
}

export interface BatchResult {
  url: string
  index: number
  success: boolean
  data: Record<string, any> | null
  error: string | null
  execution_time: number
  model_used: string | null
  fallback_attempts: number
  cached: boolean
  validation_passed: boolean | null
}

export interface BatchScrapeResponse {
  success: boolean
  results: BatchResult[]
  summary: {
    total: number
    successful: number
    failed: number
    cached: number
    total_time: number
    avg_time_per_url: number
  }
  error?: string
}

// === Metrics (Phase 4) ===

export interface MetricsStatsResponse {
  total_scrapes: number
  avg_time: number
  cache_hit_rate: number
  error_rate: number
  model_usage: Record<string, number>
}

export interface ScrapeRecord {
  id: number
  timestamp: string
  url: string
  model: string
  execution_time: number
  cached: boolean
  success: boolean
}

export interface MetricsRecentResponse {
  scrapes: ScrapeRecord[]
}

export interface MetricsStats {
  total_scrapes: number
  avg_execution_time: number
  cache_hit_rate: number
  error_rate: number
  model_usage: Record<string, number>
  recent_scrapes: ScrapeRecord[]
}

// === Configuration (Phase 4) ===

export interface ConfigResponse {
  ollama_base_url: string
  redis_host: string
  redis_port: number
  default_model: string
  default_rate_limit: string
  default_stealth_level: string
}

export interface ConfigUpdateRequest {
  ollama_base_url?: string
  redis_host?: string
  redis_port?: number
  default_model?: string
  default_rate_limit?: string
  default_stealth_level?: string
}
