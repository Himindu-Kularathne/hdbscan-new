from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "monolithic"

# ===== TEST CONFIG =====
# Set to repo folder name or None to process all
TARGET_REPO = "jpetstore-6"   # e.g. "daytrader", "acmeair", None

# ===== SUBFOLDERS =====
SEMANTIC_DIR = "semantic_data"
STATIC_DIR = "static_analysis_results"

# ===== FILES =====
SEMANTIC_PARQUET = "class_word_count.parquet"
TYPE_DATA_FILE = "typeData.json"

# ===== SEMANTIC CONFIG =====
TFIDF_TOKEN_PATTERN = r"[a-zA-Z_]{2,}"
TFIDF_MIN_DF = 1

# ===== FILTERS =====
EXCLUDE_TEST_CLASSES = True

# ===== OUTPUT CONFIG =====
OUTPUTS_ROOT = PROJECT_ROOT / "outputs"
SAVE_INTERMEDIATE = True
