# HDBSCAN Microservice Decomposition

A Python-based tool for automatically decomposing monolithic Java applications into microservices using HDBSCAN clustering on combined semantic and structural code analysis.

## Overview

This project performs:
1. **Semantic Analysis**: TF-IDF vectorization of class identifiers and documentation
2. **Structural Analysis**: Code dependency graph construction
3. **Similarity Computation**: Combined semantic + structural similarity matrices
4. **Clustering**: HDBSCAN-based class clustering for microservice decomposition

## Project Structure

```
hdbscan-new/
├── data/
│   └── monolithic/          # Source data for target repositories
│       ├── jpetstore-6/
│       ├── acmeair/
│       ├── daytrader/
│       └── [other repos]/
├── outputs/                 # Generated results
│   ├── jpetstore-6/        # Per-repo outputs
│   ├── [other repos]/
│   └── run_logs/           # Execution logs
├── schema/                 # Data format documentation
│   ├── jpetstore_data_schemas.json
│   ├── JPETSTORE_DATA_FORMATS.md
│   └── [documentation files]/
├── src/                    # Main source code
│   ├── pipeline/
│   │   └── semantic_pipeline.py    # Semantic analysis pipeline
│   ├── semantic/           # Semantic analysis modules
│   │   ├── loader.py       # Load semantic data
│   │   ├── tfidf.py        # TF-IDF computation
│   │   ├── similarity.py   # Semantic similarity
│   │   └── documents.py    # Document building
│   ├── structural/         # Structural analysis modules
│   │   ├── loader.py       # Load structural data
│   │   └── similarity.py   # Structural similarity
│   ├── combine_similarity.py       # Combine semantic + structural
│   ├── class_universe.py           # Load class definitions
│   ├── repo_discovery.py           # Discover target repositories
│   ├── config.py                   # Configuration settings
│   └── utils/
│       ├── artifacts.py    # Save/load utilities
│       └── logging.py      # Logging setup
└── scripts/                # Executable scripts
    ├── combine_sem_str.py          # Run full pipeline (recommended)
    ├── run_hdbscan.py              # Run clustering on precomputed matrices
    ├── test_semantic.py            # Test semantic pipeline
    ├── test_structural.py          # Test structural pipeline
    └── inspect_combined_matrix.py  # Inspect results
```

## Installation

### Prerequisites

- Python 3.8+
- pip or conda

### Setup

1. **Clone the repository** (if not already done)
   ```bash
   cd hdbscan-new
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install numpy pandas scipy scikit-learn hdbscan
   ```

   Or install specific versions for reproducibility:
   ```bash
   pip install numpy>=1.20.0 pandas>=1.3.0 scipy>=1.7.0 scikit-learn>=1.0.0 hdbscan>=0.8.27
   ```

## Input Data Structure

Your `data/monolithic/` directory should contain repository folders with this structure:

```
data/monolithic/
└── repository-name/
    ├── static_analysis_results/
    │   ├── typeData.json         # Class definitions and metadata
    │   └── methodData.json       # Method information
    ├── semantic_data/
    │   └── class_word_count.parquet  # TF-IDF counts (classes × terms)
    ├── structural_data/
    │   └── class_interactions.parquet # Class dependencies (edges)
    └── dynamic_analysis/         # (Optional) Runtime trace data
        └── class_per_bcs.json    # Business capability→class mapping
```

### Data Format Details

- **typeData.json**: Static type information extracted from source code AST
- **class_word_count.parquet**: Word frequency per class (DataFrame format)
- **class_interactions.parquet**: Dependency graph edges with weights
- **class_per_bcs.json**: Dynamic call chains from test execution

See `schema/JPETSTORE_DATA_INTEGRATION_GUIDE.md` for complete documentation.

## Usage

### Quick Start: Run Full Pipeline

Process one or all repositories through the complete decomposition pipeline:

```bash
# Run for a single repository (jpetstore-6)
python -m scripts.combine_sem_str
```

The script will:
1. Load class universe from static analysis
2. Compute semantic similarity (TF-IDF)
3. Compute structural similarity (dependency graph)
4. Combine both similarities with configurable weighting
5. Save outputs to `outputs/jpetstore-6/`

**Output files:**
- `combined_score_matrix.parquet` - Combined similarity matrix (dense)
- `combined_distance_matrix.npy` - Distance matrix for HDBSCAN
- `combined_meta.json` - Metadata (class names, parameters)

### Step 1: Process Semantic Data

Test or debug semantic analysis independently:

```bash
python -m scripts.test_semantic
```

**Output files** in `outputs/<repo>/semantic/`:
- `sim_sem.npy` - Semantic similarity matrix
- `meta.json` - Metadata (class names, features)
- `top_tfidf_per_class.json` - Top features per class

### Step 2: Process Structural Data

Test or debug structural analysis independently:

```bash
python -m scripts.test_structural
```

**Output files** in `outputs/<repo>/structural/`:
- `sim_str.npy` - Structural similarity matrix

### Step 3: Combine and Cluster

Run HDBSCAN clustering on the combined similarity matrix:

```bash
# Basic clustering
python -m scripts.run_hdbscan --repo jpetstore-6

# With custom parameters
python -m scripts.run_hdbscan --repo jpetstore-6 \
  --min-cluster-size 5 \
  --min-samples 3 \
  --outputs-root outputs
```

**Parameters:**
- `--repo` (required): Repository name under `outputs/`, e.g., `jpetstore-6`
- `--min-cluster-size` (default: 2): Minimum cluster size for HDBSCAN
- `--min-samples` (default: None): Minimum samples parameter
- `--outputs-root` (default: `outputs`): Output directory path

**Output files:**
- `hdbscan_clusters.json` - Cluster assignments and noise classes
- `hdbscan_labels.csv` - Class-to-cluster mapping

### Inspect Results

View combined similarity matrix statistics:

```bash
python -m scripts.inspect_combined_matrix --repo jpetstore-6
```

## Configuration

Edit `src/config.py` to customize:

```python
# Target repository (None = process all)
TARGET_REPO = "jpetstore-6"

# Weighting for combining similarities
ALPHA_STRUCTURAL = 0.5  # 50% structural, 50% semantic

# TF-IDF parameters
TFIDF_TOKEN_PATTERN = r"[a-zA-Z_]{2,}"
TFIDF_MIN_DF = 1

# Include/exclude test classes
EXCLUDE_TEST_CLASSES = True

# Output options
SAVE_INTERMEDIATE = True
```

## Output Interpretation

### hdbscan_clusters.json

```json
{
  "repo": "jpetstore-6",
  "params": {
    "min_cluster_size": 2,
    "min_samples": null,
    "metric": "precomputed"
  },
  "clusters": {
    "0": ["Account", "Order", "LineItem", ...],
    "1": ["Cart", "CartItem", ...],
    ...
  },
  "noise": ["UnusedClass", ...]
}
```

- **Cluster IDs**: Integer cluster assignments (0, 1, 2, ...)
- **Noise**: Classes labeled with -1 (not assigned to any cluster)
- **size**: Number of classes in each cluster

### Combined Matrices

- **combined_distance_matrix.npy**: Precomputed distance matrix (1 - similarity)
  - Shape: (n_classes, n_classes)
  - Used directly by HDBSCAN
  
- **combined_score_matrix.parquet**: Similarity scores (0 to 1)
  - Indexed by class names
  - Easier for human inspection

## Supported Repositories

The project includes pre-processed data for:

- **jpetstore-6** - E-commerce application (demo)
- **acmeair** - Airline booking system
- **daytrader** - Stock trading simulator
- **petclinic-legacy** - Pet clinic management
- **plants** - Plant inventory system
- **roller** - Blogging platform
- **partsunlimitedmrp** - Parts retailer

To process multiple repositories:

```python
# In src/config.py, set TARGET_REPO = None
```

Then run:
```bash
python -m scripts.combine_sem_str
```

This will process all discovered repositories sequentially.

## Processing Log

Execution logs are written to `outputs/run_logs/combine_run.log`:

```
2024-01-10 14:23:45 INFO: ▶ Combining semantic + structural similarities for: jpetstore-6
2024-01-10 14:23:46 INFO: [jpetstore-6] STEP 1: Loading class universe...
2024-01-10 14:23:47 INFO: [jpetstore-6] Classes loaded: 127
2024-01-10 14:23:48 INFO: [jpetstore-6] STEP 2: Loading semantic parquet...
2024-01-10 14:23:49 INFO: [jpetstore-6] Sim_sem shape: (127, 127)
...
```

## Troubleshooting

### "Missing: outputs/jpetstore-6/combined_distance_matrix.npy"

**Solution**: Run the full pipeline first:
```bash
python -m scripts.combine_sem_str
```

This generates the required distance matrix before clustering.

### "Monolithic data folder not found"

**Solution**: Ensure your data is in the correct location:
```bash
ls -la data/monolithic/
```

Should list repository directories (jpetstore-6, acmeair, etc.).

### "FileNotFoundError: typeData.json"

**Solution**: Verify static analysis data exists:
```bash
ls -la data/monolithic/jpetstore-6/static_analysis_results/
```

### Import errors (ModuleNotFoundError)

**Solution**: Install package in development mode from project root:
```bash
cd /path/to/hdbscan-new
python -m pip install -e .
```

Or ensure you're running scripts from the project root:
```bash
cd /path/to/hdbscan-new
python -m scripts.combine_sem_str
```

## Key Components

### Semantic Pipeline (`src/pipeline/semantic_pipeline.py`)

1. Load class universe from `typeData.json`
2. Load word-frequency data from `class_word_count.parquet`
3. Build TF-IDF matrix from documents
4. Compute cosine similarity between class vectors

**Output**: Semantic similarity matrix (n_classes × n_classes)

### Structural Pipeline (`src/structural/similarity.py`)

1. Load class interactions from `class_interactions.parquet`
2. Build adjacency matrix from edges
3. Compute similarity from graph structure (co-occurrence, common neighbors)

**Output**: Structural similarity matrix (n_classes × n_classes)

### Combination (`src/combine_similarity.py`)

Combines two similarity matrices using weighted average:

$$S_{combined} = \alpha \cdot S_{structural} + (1-\alpha) \cdot S_{semantic}$$

Where `α = ALPHA_STRUCTURAL` (default 0.5)

### HDBSCAN Clustering (`scripts/run_hdbscan.py`)

- Converts similarity to distance: `D = 1 - S`
- Clusters using precomputed distance matrix
- Groups similar classes into proposed microservices

## Performance Notes

- **Small repos** (< 200 classes): ~1-5 seconds
- **Medium repos** (200-1000 classes): ~5-30 seconds
- **Large repos** (> 1000 classes): ~30-120 seconds

Most time is spent on TF-IDF computation for large vocabularies.

## References

- Data integration guide: `schema/JPETSTORE_DATA_INTEGRATION_GUIDE.md`
- Data format reference: `schema/JPETSTORE_DATA_FORMATS.md`
- HDBSCAN algorithm: https://hdbscan.readthedocs.io/

## License

See parent project license.
