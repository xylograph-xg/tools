"""Literature Explorer 配置：全部通过环境变量覆盖，无硬编码密钥。"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE = PROJECT_ROOT.parents[2] / "paper"
DEFAULT_DB = (WORKSPACE / "fetch/crawler/literature_explorer/data/literature.db"
              if (WORKSPACE / "workspace.json").is_file()
              else Path.home() / "process/literature_explorer/literature.db")
DB_PATH = Path(os.environ.get("LITEXP_DB", DEFAULT_DB))

# OpenAlex polite pool（建议设置，无 key 也能用）
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "")
# Semantic Scholar API key（可选；无 key 时限速 1 rps 共享池）
S2_API_KEY = os.environ.get("S2_API_KEY", "")

# Embedding provider（OpenAI 兼容 /embeddings 接口；不配置则降级为词袋打分）
EMBEDDING_BASE_URL = os.environ.get("LITEXP_EMBEDDING_BASE_URL", "")
EMBEDDING_API_KEY = os.environ.get("LITEXP_EMBEDDING_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("LITEXP_EMBEDDING_MODEL", "")

REQUEST_TIMEOUT = 30
SEARCH_PER_SOURCE_LIMIT = 50
CANDIDATE_TOP_N = 30
CITATION_REFERENCE_LIMIT = 50
CITATION_FORWARD_LIMIT = 100
