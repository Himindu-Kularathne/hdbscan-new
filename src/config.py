from pathlib import Path

# Root folders
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "monolithic"

# Repo subfolders
SEMANTIC_DIR = "semantic_data"
STATIC_DIR = "static_analysis_results"

# Files
SEMANTIC_PARQUET = "class_word_count.parquet"
TYPE_DATA_FILE = "typeData.json"

# Semantic config
TFIDF_TOKEN_PATTERN = r"[a-zA-Z_]{2,}"
TFIDF_MIN_DF = 1

# Filters
EXCLUDE_TEST_CLASSES = True
