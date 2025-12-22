from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TEST_API_KEY: str
    TEST_API_BASE_URL: str
    
    # 默认测试模型，如果API没有返回特定模型列表，可以使用这个
    DEFAULT_MODEL: str = "mimo-v2-flash" 

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
