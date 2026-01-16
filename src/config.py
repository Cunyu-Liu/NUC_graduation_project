"""配置管理模块"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量 - 指定项目根目录的.env文件
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')


class Settings:
    """系统配置"""

    def __init__(self):
        # 数据库配置
        self.database_url: str = os.getenv("DATABASE_URL", "postgresql://nuc:020509@localhost:5432/literature_analysis")

        # GLM-4 API配置（智谱AI）
        self.glm_api_key: str = os.getenv("GLM_API_KEY", "")
        self.glm_base_url: str = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

        # 模型配置
        self.default_model: str = os.getenv("DEFAULT_MODEL", "glm-4-flash")
        self.default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))

        # Flask配置
        self.flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
        self.flask_port: int = int(os.getenv("FLASK_PORT", "5000"))
        self.flask_debug: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"

        # 输出目录配置
        self.output_dir: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
        self.summary_output_dir: Path = Path(os.getenv("SUMMARY_OUTPUT_DIR", "./output/summaries"))
        self.keypoints_output_dir: Path = Path(os.getenv("KEYPOINTS_OUTPUT_DIR", "./output/keypoints"))
        self.cluster_output_dir: Path = Path(os.getenv("CLUSTER_OUTPUT_DIR", "./output/clusters"))

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.summary_output_dir.mkdir(parents=True, exist_ok=True)
        self.keypoints_output_dir.mkdir(parents=True, exist_ok=True)
        self.cluster_output_dir.mkdir(parents=True, exist_ok=True)

        # 创建上传目录
        self.upload_dir = self.output_dir / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
