import sys
from pathlib import Path


# 确保 `import app.*` 在 pytest 环境下可用
# 运行目录通常是 api/，但某些环境下 sys.path 不包含该目录
API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

