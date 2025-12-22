import os
import base64

# Logo directory (relative to project root)
# Assumes this file is in core/ directory
LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo")

# Keyword mapping to filenames
LOGO_MAP = {
    "deepseek": "deepseek.png",
    "gemini": "gemini.png",
    "google": "gemini.png",
    "qwen": "qwen.png",
    "alibaba": "qwen.png",
    "通义千问": "qwen.png",
    "xiaomi": "xiaomi.png",
    "mi": "xiaomi.png",
    "小米": "xiaomi.png"
}

def get_provider_logo(provider_name: str) -> str:
    """
    Returns the absolute path to the logo file if a match is found.
    Otherwise returns None.
    """
    if not provider_name:
        return None
        
    name_lower = provider_name.lower()
    for key, filename in LOGO_MAP.items():
        if key in name_lower:
            path = os.path.join(LOGO_DIR, filename)
            if os.path.exists(path):
                return path
    return None

def get_logo_data_uri(provider_name: str) -> str:
    """
    Returns the Data URI (Base64) for the provider logo.
    Useful for Dataframes/HTML.
    """
    path = get_provider_logo(provider_name)
    if not path:
        return None
        
    try:
        with open(path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return None

# --- Tag Badge Generator ---

TAG_STYLES = {
    "new": {"color": "#FF4B4B", "icon": "✨", "text": "最新"},
    "official": {"color": "#FFC107", "icon": "🏆", "text": "官方"},
    "outdated": {"color": "#9E9E9E", "icon": "🗑️", "text": "过时"},
    "free": {"color": "#4CAF50", "icon": "🆓", "text": "免费"},
    "specialized": {"color": "#9C27B0", "icon": "🛠️", "text": "专用"},
    "preview": {"color": "#2196F3", "icon": "🧪", "text": "预览"},
    "video": {"color": "#E91E63", "icon": "🎥", "text": "视频"},
    "image": {"color": "#00BCD4", "icon": "🖼️", "text": "图像"},
    "reasoning": {"color": "#673AB7", "icon": "🧠", "text": "深度"},
    "auto": {"color": "#607D8B", "icon": "🔌", "text": "自动"},
}

def create_badge_data_uri(tags: list) -> str:
    """
    Generates a Data URI for an SVG badge based on the first recognized tag.
    Returns None if no tags match or list is empty.
    """
    if not tags:
        return None
    
    # Find first matching style
    style = None
    for tag in tags:
        if tag in TAG_STYLES:
            style = TAG_STYLES[tag]
            break
            
    if not style:
        return None
        
    color = style["color"]
    icon = style["icon"]
    text = style["text"]
    
    # Badge Dimensions
    # Unified width for consistent look (optimized for 2-char text)
    width = 52
    height = 20
    
    # SVG Content
    # Using basic SVG shapes and text
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
      <rect x="0" y="0" width="{width}" height="{height}" rx="4" fill="{color}" />
      <text x="50%" y="50%" font-family="'Microsoft YaHei', sans-serif" font-size="10" fill="white" font-weight="bold" text-anchor="middle" dominant-baseline="central">
        {icon} {text}
      </text>
    </svg>
    """
    
    # Encode to Base64
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"
