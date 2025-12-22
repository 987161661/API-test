from typing import Dict, Optional, List
import re
from pydantic import BaseModel, Field

class ModelInfo(BaseModel):
    id: str
    name: str
    provider_id: str  # e.g., "xiaomi", "deepseek", "moonshot"
    type: str  # "chat", "code", "reasoning", "vision", "audio", "video", "multimodal", "image-generation"
    context_window: int
    input_price: float  # $ per 1M tokens
    output_price: float # $ per 1M tokens
    release_date: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list) # e.g. ["new", "official", "outdated"]

class ProviderPreset(BaseModel):
    id: str
    name: str
    base_url: str
    description: str
    website: Optional[str] = None

# --- 服务商预设 ---
PROVIDER_PRESETS: List[ProviderPreset] = [
    ProviderPreset(
        id="custom",
        name="自定义 (Custom)",
        base_url="",
        description="手动输入任意 OpenAI 兼容接口地址"
    ),
    ProviderPreset(
        id="openai",
        name="OpenAI (官方)",
        base_url="https://api.openai.com/v1",
        description="GPT-4o, GPT-4o-mini, o1",
        website="https://platform.openai.com/"
    ),
    ProviderPreset(
        id="deepseek",
        name="DeepSeek (深度求索)",
        base_url="https://api.deepseek.com",
        description="DeepSeek-V3, R1 (Reasoning)",
        website="https://platform.deepseek.com/"
    ),
    ProviderPreset(
        id="moonshot",
        name="Moonshot (Kimi)",
        base_url="https://api.moonshot.cn/v1",
        description="Kimi 8k/32k/128k",
        website="https://platform.moonshot.cn/"
    ),
    ProviderPreset(
        id="zhipu",
        name="ZhipuAI (智谱清言)",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        description="GLM-4, GLM-4-Flash",
        website="https://open.bigmodel.cn/"
    ),
    ProviderPreset(
        id="qwen",
        name="Alibaba Qwen (通义千问)",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Qwen-Plus, Qwen-Max",
        website="https://bailian.console.aliyun.com/"
    ),
    ProviderPreset(
        id="xiaomi",
        name="Xiaomi (小米)",
        base_url="https://api.xiaomimimo.com/v1",
        description="MiMo-V2",
        website="https://admin.xiaomimimo.com/"
    ),
    ProviderPreset(
        id="gemini",
        name="Google Gemini (OpenAI Compatible)",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/", 
        description="Gemini 2.0/2.5 Flash, 3.0 Pro (需API Key)",
        website="https://aistudio.google.com/"
    ),
]

# 预定义模型元数据
MODEL_METADATA: Dict[str, ModelInfo] = {
    # --- Xiaomi MiMo ---
    "mimo-v2-flash": ModelInfo(
        id="mimo-v2-flash",
        name="MiMo-V2-Flash",
        tags=["new"],
        provider_id="xiaomi",
        type="chat",
        context_window=256000,
        input_price=0.10,
        output_price=0.30,
        release_date="2025-12-16",
        description="309B MoE model, 150 tok/s, 256k context."
    ),
    
    # --- DeepSeek ---
    "deepseek-chat": ModelInfo(
        id="deepseek-chat",
        name="DeepSeek-V3",
        tags=["official"],
        provider_id="deepseek",
        type="chat",
        context_window=64000,
        input_price=0.14, 
        output_price=0.28,
        release_date="2024-12-26",
        description="Strong general purpose chat model."
    ),
    "deepseek-reasoner": ModelInfo(
        id="deepseek-reasoner",
        name="DeepSeek-R1",
        tags=["official"],
        provider_id="deepseek",
        type="reasoning",
        context_window=64000,
        input_price=0.55, 
        output_price=2.19,
        release_date="2025-01-20",
        description="Specialized in complex reasoning tasks."
    ),
    "deepseek-v3.2": ModelInfo(
        id="deepseek-v3.2",
        name="DeepSeek-V3.2",
        tags=["new"],
        provider_id="deepseek",
        type="chat",
        context_window=128000,
        input_price=0.20, # Estimated
        output_price=0.40,
        release_date="2025-12-19",
        description="Updated DeepSeek V3 model."
    ),
     "deepseek-r1": ModelInfo(
        id="deepseek-r1",
        name="DeepSeek-R1 (Full)",
        tags=["official"],
        provider_id="deepseek",
        type="reasoning",
        context_window=64000,
        input_price=0.55,
        output_price=2.19,
        release_date="2025-01-20",
        description="Full DeepSeek R1 reasoning model."
    ),

    # --- Moonshot / Kimi ---
    "moonshot-v1-8k": ModelInfo(
        id="moonshot-v1-8k",
        name="Kimi-v1 8k",
        tags=["outdated"],
        provider_id="moonshot",
        type="chat",
        context_window=8192,
        input_price=0.15,
        output_price=0.60,
        release_date="2023-10-09",
        description="Standard context Kimi model."
    ),
    "moonshot-v1-32k": ModelInfo(
        id="moonshot-v1-32k",
        name="Kimi-v1 32k",
        tags=["outdated"],
        provider_id="moonshot",
        type="chat",
        context_window=32768,
        input_price=0.15,
        output_price=0.60,
        release_date="2023-10-09",
        description="Medium context Kimi model."
    ),
    "moonshot-v1-128k": ModelInfo(
        id="moonshot-v1-128k",
        name="Kimi-v1 128k",
        tags=["official"],
        provider_id="moonshot",
        type="chat",
        context_window=128000,
        input_price=0.15,
        output_price=0.60,
        release_date="2023-10-09",
        description="Long context Kimi model."
    ),
    "kimi-k2-thinking": ModelInfo(
        id="kimi-k2-thinking",
        name="Kimi K2 Thinking",
        tags=["new"],
        provider_id="moonshot",
        type="reasoning",
        context_window=128000,
        input_price=0.30, # Estimated
        output_price=1.20,
        release_date="2025-11-20",
        description="New generation reasoning model from Moonshot."
    ),
    
    # --- Qwen (Alibaba) ---
    "qwen-plus": ModelInfo(
        id="qwen-plus",
        name="Qwen-Plus",
        tags=["official"],
        provider_id="qwen",
        type="chat",
        context_window=1048576,  # 1M
        input_price=0.40,
        output_price=1.20,
        release_date="2025-12-15",
        description="Powered by Qwen 3. Balanced performance."
    ),
    "qwen-turbo": ModelInfo(
        id="qwen-turbo",
        name="Qwen-Turbo",
        tags=["outdated"],
        provider_id="qwen",
        type="chat",
        context_window=1048576,  # 1M
        input_price=0.05,
        output_price=0.20,
        release_date="2024-06-07",
        description="Fast/Cost-effective, being replaced by Flash."
    ),
    "qwen-max": ModelInfo(
        id="qwen-max",
        name="Qwen-Max",
        tags=["official"],
        provider_id="qwen",
        type="chat",
        context_window=32768,
        input_price=1.60,
        output_price=6.40,
        release_date="2025-12-15",
        description="Powered by Qwen 3. Top-tier performance."
    ),
    "qwen-flash": ModelInfo(
        id="qwen-flash",
        name="Qwen-Flash",
        tags=["new"],
        provider_id="qwen",
        type="chat",
        context_window=1048576, # 1M
        input_price=0.01,
        output_price=0.02,
        release_date="2024-09-19",
        description="Fastest & cheapest, 1M context."
    ),
    "qwen-long": ModelInfo(
        id="qwen-long",
        name="Qwen-Long",
        tags=["specialized"],
        provider_id="qwen",
        type="chat",
        context_window=10000000, # Up to 10M
        input_price=0.05,
        output_price=0.20,
        release_date="2024-09-19",
        description="Specialized for extremely long context (up to 10M)."
    ),
    "qwen-vl-max": ModelInfo(
        id="qwen-vl-max",
        name="Qwen-VL-Max",
        tags=["official"],
        provider_id="qwen",
        type="vision",
        context_window=32768,
        input_price=0.00, # Varies by image/video resolution
        output_price=0.00,
        release_date="2024-08-07",
        description="Top-tier multimodal model."
    ),
    "qwen-vl-plus": ModelInfo(
        id="qwen-vl-plus",
        name="Qwen-VL-Plus",
        tags=["outdated"],
        provider_id="qwen",
        type="vision",
        context_window=32768,
        input_price=0.00,
        output_price=0.00,
        release_date="2024-01-26",
        description="Balanced multimodal model."
    ),
    "qwen3-vl-plus-2025-12-19": ModelInfo(
        id="qwen3-vl-plus-2025-12-19",
        name="Qwen3-VL-Plus (1219)",
        tags=["new"],
        provider_id="qwen",
        type="vision",
        context_window=32768,
        input_price=0.40,
        output_price=1.20,
        release_date="2025-12-19",
        description="Newest Qwen3 Vision-Language Plus model."
    ),
    "qwen3-omni-flash-2025-12-01": ModelInfo(
        id="qwen3-omni-flash-2025-12-01",
        name="Qwen3-Omni-Flash (1201)",
        tags=["new"],
        provider_id="qwen",
        type="multimodal",
        context_window=32768,
        input_price=0.02,
        output_price=0.04,
        release_date="2025-12-01",
        description="Omni-modal flash model for fast interactions."
    ),
    "qwen3-omni-flash-realtime-2025-12-01": ModelInfo(
        id="qwen3-omni-flash-realtime-2025-12-01",
        name="Qwen3-Omni-Flash Realtime",
        tags=["new"],
        provider_id="qwen",
        type="multimodal",
        context_window=32768,
        input_price=0.02,
        output_price=0.04,
        release_date="2025-12-01",
        description="Realtime omni-modal capabilities."
    ),
    "qwen-coder-plus": ModelInfo(
        id="qwen-coder-plus",
        name="Qwen-Coder-Plus",
        tags=["new"],
        provider_id="qwen",
        type="code",
        context_window=128000,
        input_price=2.50,
        output_price=10.00,
        release_date="2025-12-15",
        description="Specialized coding model powered by Qwen3."
    ),
    "qwen-mt-plus": ModelInfo(
        id="qwen-mt-plus",
        name="Qwen-MT-Plus",
        tags=["new"],
        provider_id="qwen",
        type="chat",
        context_window=32768,
        input_price=0.00, 
        output_price=0.00,
        release_date="2025-12-15",
        description="Flagship translation model, powered by Qwen3."
    ),
    
    # --- OpenAI (Reference) ---
    "gpt-3.5-turbo": ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        tags=["outdated"],
        provider_id="openai",
        type="chat",
        context_window=16385,
        input_price=0.50,
        output_price=1.50,
        release_date="2023-03-01",
        description="Legacy standard."
    ),
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        tags=["official"],
        provider_id="openai",
        type="chat/vision",
        context_window=128000,
        input_price=2.50,
        output_price=10.00,
        release_date="2024-05-13",
        description="Omni model."
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o-Mini",
        tags=["official"],
        provider_id="openai",
        type="chat/vision",
        context_window=128000,
        input_price=0.15,
        output_price=0.60,
        release_date="2024-07-18",
        description="Cost-effective small model."
    ),
    "o1-preview": ModelInfo(
        id="o1-preview",
        name="o1 Preview",
        tags=["new"],
        provider_id="openai",
        type="reasoning",
        context_window=128000,
        input_price=15.00,
        output_price=60.00,
        release_date="2024-09-12",
        description="Advanced reasoning model."
    ),

    # --- Zhipu AI (GLM) ---
    "glm-4": ModelInfo(
        id="glm-4",
        name="GLM-4",
        tags=["outdated"],
        provider_id="zhipu",
        type="chat",
        context_window=128000,
        input_price=1.40, 
        output_price=1.40,
        release_date="2024-01-16",
        description="Zhipu flagship model."
    ),
    "glm-4-flash": ModelInfo(
        id="glm-4-flash",
        name="GLM-4-Flash",
        tags=["free"],
        provider_id="zhipu",
        type="chat",
        context_window=128000,
        input_price=0.00,
        output_price=0.00,
        release_date="2024-05-28",
        description="High speed, very low cost (often free)."
    ),
    "glm-4-air": ModelInfo(
        id="glm-4-air",
        name="GLM-4-Air",
        tags=["official"],
        provider_id="zhipu",
        type="chat",
        context_window=128000,
        input_price=0.14,
        output_price=0.14,
        release_date="2024-06-05",
        description="Balanced price/performance."
    ),

    # --- Google Gemini ---
    "gemini-3-pro-preview": ModelInfo(
        id="gemini-3-pro-preview",
        name="Gemini 3 Pro",
        tags=["new", "preview"],
        provider_id="google",
        type="chat/vision/audio/video",
        context_window=2097152,
        input_price=2.00,
        output_price=12.00,
        release_date="2025-11-18",
        description="Most powerful multimodal & agentic model."
    ),
    "gemini-2.5-pro": ModelInfo(
        id="gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        tags=["new"],
        provider_id="google",
        type="chat/vision/audio/video",
        context_window=2097152,
        input_price=1.25,
        output_price=10.00,
        release_date="2025-06-17",
        description="Best for coding & reasoning. 2M context."
    ),
    "gemini-2.5-flash": ModelInfo(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        tags=["new"],
        provider_id="google",
        type="chat/vision/audio/video",
        context_window=1048576,
        input_price=0.30,
        output_price=2.50,
        release_date="2025-06-17",
        description="Hybrid reasoning, balanced intelligence/latency."
    ),
    "gemini-2.5-flash-lite": ModelInfo(
        id="gemini-2.5-flash-lite",
        name="Gemini 2.5 Flash-Lite",
        tags=["new"],
        provider_id="google",
        type="chat/vision",
        context_window=1048576,
        input_price=0.10,
        output_price=0.40,
        release_date="2025-09-01",
        description="Most cost-effective 2.5 model."
    ),
    "gemini-2.0-flash": ModelInfo(
        id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        tags=["outdated"],
        provider_id="google",
        type="chat/vision/audio",
        context_window=1048576,
        input_price=0.10,
        output_price=0.40,
        release_date="2024-12-11",
        description="Balanced multimodal workhorse."
    ),
    "gemini-2.0-flash-lite": ModelInfo(
        id="gemini-2.0-flash-lite",
        name="Gemini 2.0 Flash-Lite",
        tags=["outdated"],
        provider_id="google",
        type="chat/vision",
        context_window=1048576,
        input_price=0.08,
        output_price=0.30,
        release_date="2025-02-05",
        description="Fastest & cheapest generation."
    ),
    "gemini-1.5-pro": ModelInfo(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        tags=["outdated"],
        provider_id="google",
        type="chat/vision",
        context_window=2097152,
        input_price=1.25,
        output_price=5.00,
        release_date="2024-02-15",
        description="Google's previous flagship, 2M context."
    ),
    "gemini-1.5-flash": ModelInfo(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        tags=["outdated"],
        provider_id="google",
        type="chat/vision",
        context_window=1048576,
        input_price=0.075,
        output_price=0.30,
        release_date="2024-05-14",
        description="Fast and cost-efficient, 1M context."
    ),
    "veo-3.1-generate-preview": ModelInfo(
        id="veo-3.1-generate-preview",
        name="Veo 3.1 Preview",
        tags=["new", "video"],
        provider_id="google",
        type="video-generation",
        context_window=0, # Generation model
        input_price=0.00,
        output_price=0.00,
        release_date="2025-12-01",
        description="State-of-the-art video generation model."
    ),
    "veo-3.1-fast-generate-preview": ModelInfo(
        id="veo-3.1-fast-generate-preview",
        name="Veo 3.1 Fast Preview",
        tags=["new", "video"],
        provider_id="google",
        type="video-generation",
        context_window=0,
        input_price=0.00,
        output_price=0.00,
        release_date="2025-12-01",
        description="Faster variant of Veo 3.1."
    ),
    "imagen-4.0-generate-preview-06-06": ModelInfo(
        id="imagen-4.0-generate-preview-06-06",
        name="Imagen 4.0 Preview",
        tags=["new", "image"],
        provider_id="google",
        type="image-generation",
        context_window=0,
        input_price=0.00,
        output_price=0.00,
        release_date="2025-06-06",
        description="Next-gen image generation."
    ),
    "deep-research-pro-preview-12-2025": ModelInfo(
        id="deep-research-pro-preview-12-2025",
        name="Deep Research Pro",
        tags=["new", "reasoning"],
        provider_id="google",
        type="reasoning",
        context_window=128000,
        input_price=5.00,
        output_price=15.00,
        release_date="2025-12-01",
        description="Specialized model for deep research tasks."
    ),
}

def get_model_info(model_id: str) -> ModelInfo:
    """Retrieve model info with fallback and intelligent date extraction."""
    
    # Helper to extract date from ID (e.g. 2025-05-07 or 20250507)
    def extract_date(s: str) -> Optional[str]:
        # Pattern 1: YYYY-MM-DD
        match = re.search(r'20[2-9]\d-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])', s)
        if match:
            return match.group(0)
        # Pattern 2: YYYYMMDD
        match = re.search(r'20[2-9]\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])', s)
        if match:
            d = match.group(0)
            return f"{d[:4]}-{d[4:6]}-{d[6:]}"
        return None

    def infer_type(s: str) -> str:
        mid = s.lower()
        # Image Generation
        if any(k in mid for k in ["dall-e", "flux", "stable-diffusion", "midjourney", "imagen", "text-to-image", "image-gen", "gen-image"]):
            return "image-generation"
        # Video Generation
        if any(k in mid for k in ["sora", "runway", "pika", "kling", "luma", "cogvideo", "text-to-video", "video-gen", "gen-video", "veo"]):
            return "video-generation"
        # Audio Generation (TTS / Music)
        if any(k in mid for k in ["tts", "speech", "voice", "suno", "udio", "text-to-audio", "audio-gen", "gen-audio"]):
            return "audio-generation"
        # Audio Transcription
        if any(k in mid for k in ["whisper", "stt", "speech-to-text"]):
            return "audio-transcription"
        # Embedding
        if any(k in mid for k in ["embed", "embedding"]):
            return "embedding"
        # Default unknown
        return "unknown"

    extracted_date = extract_date(model_id)
    inferred_type = infer_type(model_id)

    # Try exact match
    if model_id in MODEL_METADATA:
        info = MODEL_METADATA[model_id]
        return info
    
    # Try partial match (e.g. version suffixes like -001, -latest, -exp)
    # We prioritize matching the longest key to avoid ambiguous matches
    sorted_keys = sorted(MODEL_METADATA.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in model_id:
            info = MODEL_METADATA[key]
            
            # Prepare updates
            updates = {"id": model_id}
            if extracted_date:
                updates["release_date"] = extracted_date
                
            # Return a copy with the actual ID and potentially updated date
            return info.model_copy(update=updates)
            
    # Fallback for unknown models
    return ModelInfo(
        id=model_id,
        name=f"{model_id}", # Restore clean name
        tags=["auto"], # Add auto tag
        provider_id="unknown",
        type=inferred_type,  # Use inferred type instead of "unknown"
        context_window=0,
        input_price=0.0,
        output_price=0.0,
        release_date=extracted_date,
        description="此模型由 API 自动发现，未收录详细元数据 (Context, Price, etc.)。"
    )
