/**
 * AI provider settings (localStorage, ocppautomation-compatible).
 */

export type AIProvider = "claude" | "openai" | "gemini" | "ollama";
export type AISelectionMode = AIProvider | "hybrid";

export const AI_CONFIG_KEY = "csautobot_ai_config";

export const AI_PROVIDER_ORDER: AIProvider[] = ["ollama", "claude", "openai", "gemini"];

export const AI_PROVIDER_INFO: Record<
  AIProvider,
  { label: string; description: string; icon: string }
> = {
  claude: {
    label: "Claude (Anthropic)",
    description: "200K context, best for long documents",
    icon: "🟣",
  },
  openai: {
    label: "OpenAI (GPT-4o)",
    description: "JSON mode, reliable structured output",
    icon: "🟢",
  },
  gemini: {
    label: "Google Gemini",
    description: "Fast, cost-effective",
    icon: "🔵",
  },
  ollama: {
    label: "Ollama (Local LLM)",
    description: "Privacy-first, no API key needed",
    icon: "🏠",
  },
};

export const AI_SELECTION_INFO: Record<
  AISelectionMode,
  { label: string; description: string; icon: string }
> = {
  ...AI_PROVIDER_INFO,
  hybrid: {
    label: "Hybrid (Fallback)",
    description: "여러 AI를 순차 시도하여 실패 시 자동 전환",
    icon: "🧩",
  },
};

export interface StoredAIConfig {
  provider: AISelectionMode;
  hybridProviders?: AIProvider[];
  apiKeys: Partial<Record<AIProvider, string>>;
  models: Partial<Record<AIProvider, string>>;
  ollamaBaseUrl?: string;
}

const OUTDATED_CLAUDE_MODELS = new Set([
  "claude-sonnet-4-20250514",
  "claude-sonnet-4-5",
  "claude-3-5-sonnet-20241022",
  "claude-3-opus-20240229",
  "claude-3-sonnet-20240229",
]);

export const DEFAULT_AI_CONFIG: StoredAIConfig = {
  provider: "hybrid",
  hybridProviders: [...AI_PROVIDER_ORDER],
  apiKeys: {},
  models: {
    claude: "claude-sonnet-4-6",
    openai: "gpt-4o",
    gemini: "gemini-2.0-flash",
    ollama: "qwen3:8b",
  },
  ollamaBaseUrl: "http://localhost:11434",
};

export function isAIProvider(value: AISelectionMode): value is AIProvider {
  return value !== "hybrid";
}

export function loadAIConfig(): StoredAIConfig {
  if (typeof window === "undefined") return DEFAULT_AI_CONFIG;
  try {
    const raw = localStorage.getItem(AI_CONFIG_KEY);
    if (!raw) return DEFAULT_AI_CONFIG;
    const config: StoredAIConfig = { ...DEFAULT_AI_CONFIG, ...JSON.parse(raw) };

    if (config.models?.claude && OUTDATED_CLAUDE_MODELS.has(config.models.claude)) {
      config.models = { ...config.models, claude: DEFAULT_AI_CONFIG.models.claude! };
      saveAIConfig(config);
    }

    return config;
  } catch {
    return DEFAULT_AI_CONFIG;
  }
}

export function saveAIConfig(config: StoredAIConfig): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(AI_CONFIG_KEY, JSON.stringify(config));
  } catch (e) {
    console.error("[AI Config] Failed to save:", e);
  }
}

/** FastAPI request body (snake_case). */
export function buildAiConfigPayload(config?: StoredAIConfig) {
  const cfg = config ?? loadAIConfig();
  return {
    provider: cfg.provider,
    hybrid_providers: cfg.hybridProviders?.length ? cfg.hybridProviders : AI_PROVIDER_ORDER,
    api_keys: cfg.apiKeys ?? {},
    models: cfg.models ?? {},
    ollama_base_url: cfg.ollamaBaseUrl ?? "http://localhost:11434",
  };
}
