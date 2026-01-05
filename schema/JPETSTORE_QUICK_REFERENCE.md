# JPetStore-6 Data Formats - Quick Reference Guide

## 📋 File Locations & Formats

```
jpetstore-6/
├── dynamic_analysis/
│   └── class_per_bcs.json              # JSON: Test→Classes mapping
├── semantic_data/
│   └── class_word_count.parquet        # Parquet: Class→Words→Frequency
├── static_analysis_results/
│   ├── typeData.json                   # JSON: Complete type definitions
│   └── methodData.json                 # JSON: Method-level details
└── structural_data/
    └── class_interactions.parquet      # Parquet: Class relationships
```

---

## 🔍 Quick Data Lookup

### 1. "I need to find all methods in a class"
**Use:** `typeData.json`
```python
# Find Account class
account = [t for t in typeData if t['fullName'] == 'org.mybatis.jpetstore.domain.Account'][0]

# Get methods
methods = account['methods']
# Output: ['getUsername()', 'setPassword(java.lang.String)', ...]
```

### 2. "I need to know what a test case tests"
**Use:** `class_per_bcs.json`
```python
# Find classes accessed by a test
classes = class_per_bcs['CartTest_addItemWhenIsInStockIsTrue()']
# Output: ['org.mybatis.jpetstore.domain.CartTest', 'org.mybatis.jpetstore.domain.Item', ...]
```

### 3. "I need to find dependencies between classes"
**Use:** `typeData.json` + `class_interactions.parquet`
```python
# From typeData - direct references
account_deps = account_type['referencedTypes']

# From class_interactions - structural relationships
from_order = interactions[interactions['source_class'] == 'Order']
to_lineitem = from_order[from_order['target_class'] == 'LineItem']
```

### 4. "I need semantically similar classes"
**Use:** `class_word_count.parquet`
```python
# Get all words in Account class
account_words = word_counts[word_counts['class_name'] == 'Account']
# Count common words with other classes (Jaccard/cosine similarity)
```

### 5. "I need the class hierarchy"
**Use:** `typeData.json`
```python
account = find_by_name('Account')
# Parent classes
parents = account['inheritedTypes']
# All classes implementing Serializable
children = [t for t in typeData if 'Serializable' in t['inheritedTypes']]
```

---

## 📊 Data Statistics

| Data Source | Format | Records | Size | Primary Key |
|------------|--------|---------|------|------------|
| `typeData.json` | JSON | 49 classes | ~50KB | `fullName` |
| `class_per_bcs.json` | JSON | ~80 entries | ~30KB | method signature |
| `class_word_count.parquet` | Parquet | ~1000+ rows | ~200KB | class_name + word |
| `class_interactions.parquet` | Parquet | ~100-500 edges | ~50KB | source + target |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Presentation Layer (web.actions)                   │
│  AccountActionBean, OrderActionBean, etc.           │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Business Logic Layer (service)                     │
│  AccountService, OrderService, CatalogService       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Data Access Layer (mapper)                         │
│  AccountMapper, OrderMapper, ItemMapper, etc.       │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  Domain Layer (domain)                              │
│  Account, Order, Product, Cart, LineItem, etc.      │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Common Analysis Tasks

### Task 1: Identify tightly coupled classes
```python
# Classes with many dependencies
for type_info in typeData:
    deps = type_info['referencedTypes']
    if len(deps) > 10:
        print(f"{type_info['simpleName']} has {len(deps)} dependencies")
```

### Task 2: Find classes involved in order processing
```python
# Dynamic: find test cases about orders
order_tests = [k for k in class_per_bcs.keys() if 'Order' in k]

# Static: find Order-related classes
order_classes = [t for t in typeData if 'Order' in t['fullName']]

# Structural: find what depends on Order
order_deps = interactions[interactions['target_class'].str.contains('Order')]
```

### Task 3: Trace a microservice boundary
```python
# Start with one class
service_type = find_by_name('org.mybatis.jpetstore.service.OrderService')

# Get all its dependencies
deps = service_type['referencedTypes']

# Recursively get dependencies of those (2 levels deep)
all_involved = set(deps)
for dep in deps:
    dep_type = find_by_name(dep)
    if dep_type:
        all_involved.update(dep_type['referencedTypes'])

# Filter to only internal classes (not java.*)
internal = [d for d in all_involved if not d.startswith('java.')]
```

### Task 4: Test coverage analysis
```python
# Which classes are tested?
tested_classes = set()
for method, classes in class_per_bcs.items():
    tested_classes.update(classes)

# Which domain classes are NOT tested?
domain_classes = {t['fullName'] for t in typeData if t.is_domain_class()}
untested = domain_classes - tested_classes
```

### Task 5: Identify candidate components
```python
# Group by package
packages = {}
for type_info in typeData:
    pkg = type_info['fullName'].rsplit('.', 1)[0]
    if pkg not in packages:
        packages[pkg] = []
    packages[pkg].append(type_info['fullName'])

# Calculate intra-package cohesion
for pkg, classes in packages.items():
    interactions_within = interactions[
        (interactions['source_class'].isin(classes)) &
        (interactions['target_class'].isin(classes))
    ]
    print(f"{pkg}: {len(interactions_within)} internal interactions")
```

---

## 🔗 Data Integration Examples

### Example 1: Build Complete Dependency Graph
```python
import networkx as nx

# Create directed graph
G = nx.DiGraph()

# Add nodes from typeData
for type_info in typeData:
    G.add_node(type_info['fullName'])

# Add edges from class_interactions
for _, row in interactions.iterrows():
    G.add_edge(row['source_class'], row['target_class'], 
               weight=row['weight'])

# Find all dependencies of OrderService
from_service = nx.descendants(G, 'org.mybatis.jpetstore.service.OrderService')
```

### Example 2: Semantic + Structural Analysis
```python
# Find semantically similar classes that are NOT structurally related
similar_classes = find_similar('Account', top_k=10)

for sim_class, score in similar_classes:
    # Check if they interact
    interact = interactions[
        ((interactions['source_class'] == 'Account') & 
         (interactions['target_class'] == sim_class)) |
        ((interactions['source_class'] == sim_class) & 
         (interactions['target_class'] == 'Account'))
    ]
    
    if interact.empty:
        print(f"{sim_class} is similar ({score:.2%}) but not connected")
```

### Example 3: Dynamic + Static Analysis
```python
# For each test, find potential issues
for test_method, accessed_classes in class_per_bcs.items():
    # Check if all accessed classes are in same component
    
    # Find dependencies not directly accessed
    type_objs = [find_by_name(c) for c in accessed_classes]
    transitive_deps = set()
    for t in type_objs:
        if t:
            transitive_deps.update(t['referencedTypes'])
    
    missing = transitive_deps - set(accessed_classes)
    if missing:
        print(f"{test_method} may be missing these classes: {missing}")
```

---

## 🐍 Python One-Liners

```python
# Count classes by type
print(sum(1 for t in typeData if t['isInterface']))           # interfaces
print(sum(1 for t in typeData if not t['isInterface']))       # classes

# Find methods with most parameters
max_params = max((t, len(t['parameterTypes'])) 
                 for t in typeData)

# Most referenced type
from collections import Counter
all_refs = []
for t in typeData:
    all_refs.extend(t['referencedTypes'])
most_common = Counter(all_refs).most_common(1)

# Cyclomatic-like metric: methods per class
methods_per_class = {t['simpleName']: len(t['methods']) 
                     for t in typeData}

# Class coupling: external dependencies
external_deps = {t['simpleName']: 
                 len([r for r in t['referencedTypes'] 
                      if not r.startswith('java.')]) 
                 for t in typeData}
```

---

## 📈 Metrics You Can Compute

| Metric | Formula | Data Source |
|--------|---------|-------------|
| **Coupling** | # external types referenced | typeData |
| **Cohesion** | internal interactions / total interactions | class_interactions |
| **Inheritance Depth** | max distance in inheritance tree | typeData |
| **Fan-In** | # classes depending on this class | class_interactions |
| **Fan-Out** | # classes this class depends on | typeData |
| **Test Coverage** | # tested classes / total classes | class_per_bcs |
| **Modularity** | internal coupling / external coupling | combined |

---

## 🔑 Key Types in JPetStore

### Domain Classes
- `Account`, `Product`, `Category`, `Item` - Catalog
- `Order`, `LineItem` - Orders
- `Cart`, `CartItem` - Shopping Cart

### Service Classes
- `AccountService` - User management
- `CatalogService` - Product browsing
- `OrderService` - Order processing

### Mapper Interfaces
- `AccountMapper`, `ProductMapper`, `ItemMapper`
- `OrderMapper`, `LineItemMapper`, `CategoryMapper`
- `SequenceMapper` - ID generation

### Action Beans (Controllers)
- `AccountActionBean` - Account management
- `CatalogActionBean` - Product browsing
- `CartActionBean` - Shopping cart
- `OrderActionBean` - Order management

---

## 💡 Tips for LLM Prompting

When asking an LLM to generate code based on this data:

1. **Provide the relevant TypeInfo objects** in the prompt
2. **Specify the interaction types** you're interested in
3. **Include class method signatures** for API contracts
4. **Reference the layer architecture** for separation of concerns
5. **Use metrics like coupling** to justify design choices

Example prompt:
```
Given these classes (as TypeInfo objects):
[Account TypeInfo, Order TypeInfo, LineItem TypeInfo]

And these structural relationships:
(Order -> LineItem: composition)
(Order -> Account: dependency)

Generate a Java service class that processes orders...
```

---

## 🚀 Quick Start Python Script

```python
import json
import pandas as pd
from pathlib import Path

# Load all data
base = Path('/path/to/jpetstore-6')

with open(base / 'static_analysis_results' / 'typeData.json') as f:
    types = json.load(f)

with open(base / 'dynamic_analysis' / 'class_per_bcs.json') as f:
    bcs = json.load(f)

interactions = pd.read_parquet(base / 'structural_data' / 'class_interactions.parquet')
words = pd.read_parquet(base / 'semantic_data' / 'class_word_count.parquet')

# Quick queries
print(f"Total types: {len(types)}")
print(f"Total interactions: {len(interactions)}")
print(f"Test cases: {len(bcs)}")

# Find a class
account = [t for t in types if t['fullName'] == 'org.mybatis.jpetstore.domain.Account'][0]
print(f"\nAccount methods: {account['methods']}")

# Find interactions
account_interactions = interactions[interactions['target_class'].str.contains('Account')]
print(f"\nClasses interacting with Account: {len(account_interactions)}")
```

---

## 🔗 Related Files

- `JPETSTORE_DATA_FORMATS.md` - Comprehensive format documentation
- `jpetstore_data_format_reference.py` - Python API reference
- `jpetstore_data_schemas.json` - JSON Schema definitions
