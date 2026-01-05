# JPetStore-6 Data Formats Reference

## Overview
JPetStore-6 provides four distinct categories of analysis data: **Dynamic**, **Semantic**, **Static**, and **Structural**. This document describes the format and structure of each dataset to enable LLMs and other tools to parse and utilize the data effectively.

---

## 1. Dynamic Analysis Data

### File: `dynamic_analysis/class_per_bcs.json`

**Purpose:** Maps test/execution methods to the classes they interact with during execution.

**Format:** Key-Value JSON object where:
- **Key (String):** Test/method identifier in format `ClassName_methodName()` or `ClassName_methodNameOutputResult()`
- **Value (Array[String]):** List of fully qualified class names that are accessed/invoked during this method's execution

**Example Structure:**
```json
{
  "OrderActionBeanTest_getOrderListOutputNull()": [
    "org.mybatis.jpetstore.web.actions.OrderActionBeanTest",
    "org.mybatis.jpetstore.web.actions.OrderActionBean"
  ],
  "CartTest_addItemWhenIsInStockIsTrue()": [
    "org.mybatis.jpetstore.domain.CartTest",
    "org.mybatis.jpetstore.domain.Item",
    "org.mybatis.jpetstore.domain.Cart",
    "org.mybatis.jpetstore.domain.CartItem"
  ]
}
```

**Usage:**
- Track which classes are involved in specific test cases
- Identify Behavioral Component Slices (BCS)
- Understand class dependencies through runtime behavior
- Trace execution paths and component interactions

**Data Characteristics:**
- **Total entries:** ~80+ method executions
- **Classes per entry:** 1-6+ classes
- **Relationship type:** Runtime execution traces

---

## 2. Semantic Analysis Data

### File: `semantic_data/class_word_count.parquet`

**Purpose:** Semantic representation of classes using word/token frequency analysis.

**Format:** Apache Parquet columnar format
- Optimized for compression and efficient querying
- Contains class names and their semantic tokens with occurrence counts

**Typical Schema (inferred):**
```
Columns:
  - class_name: String (fully qualified class name)
  - word: String (semantic token/word from code, javadoc, etc.)
  - count: Integer (frequency of this word in the class)
```

**Example Interpretation:**
```
class_name: "org.mybatis.jpetstore.domain.Account"
word: "password"
count: 5

class_name: "org.mybatis.jpetstore.domain.Account"
word: "username"
count: 7
```

**Usage:**
- Build semantic embeddings/vectors for classes
- Similarity analysis between classes based on vocabulary
- Topic modeling and semantic clustering
- Document similarity using TF-IDF or similar metrics
- Natural language understanding of code semantics

**Data Characteristics:**
- **Format:** Apache Parquet (binary, columnar)
- **Rows:** Multiple words per class, total ~thousands of rows
- **Compression:** Efficient for large-scale analysis
- **Query pattern:** Can select specific classes or words efficiently

---

## 3. Static Analysis Data

### File A: `static_analysis_results/typeData.json`

**Purpose:** Complete type hierarchy and structural information for all Java classes, interfaces, and enums.

**Format:** JSON Array of type objects

**Complete Object Schema:**

```typescript
interface TypeData {
  isInterface: boolean;
  isImplicit: boolean;
  isAnnotation: boolean;
  isAnonymous: boolean;
  simpleName: string;                    // "Account"
  fullName: string;                      // "org.mybatis.jpetstore.domain.Account"
  
  // Type information
  referencedTypes: string[];              // All types referenced by this class
  nestedTypes: string[];                  // Inner classes
  inheritedTypes: string[];               // Parent classes/interfaces
  
  // Fields
  fieldTypes: string[];                   // Types of all fields
  
  // Methods
  parameterTypes: string[];               // All parameter types used
  returnTypes: string[];                  // All return types
  constructors: string[];                 // Constructor signatures
  methods: string[];                      // All method signatures
  
  // Field calls (inter-field dependencies)
  fieldCalls: Array<{
    invokingObject: string;               // Class calling the field
    invokingMethod: string;               // Method doing the calling
    invokedObject: string;                // Class being called (e.g., Collections)
    invokedMethod: string;                // Static method being called
    local: boolean;                       // Is it a local call?
  }>;
  
  // Text and names (debugging/display)
  textAndNames: string[];                 // All identifiers, method names, field names
}
```

**Example - Domain Class (Account):**
```json
{
  "isInterface": false,
  "isImplicit": false,
  "isAnnotation": false,
  "isAnonymous": false,
  "simpleName": "Account",
  "fullName": "org.mybatis.jpetstore.domain.Account",
  "referencedTypes": [
    "org.mybatis.jpetstore.domain.Account",
    "boolean",
    "void",
    "net.sourceforge.stripes.validation.Validate",
    "java.lang.String",
    "java.io.Serializable"
  ],
  "fieldTypes": [
    "long",
    "java.lang.String",
    "java.lang.String",
    "java.lang.String"
  ],
  "parameterTypes": [
    "java.lang.String",
    "long",
    "boolean"
  ],
  "returnTypes": [
    "void",
    "java.lang.String",
    "boolean"
  ],
  "inheritedTypes": ["java.io.Serializable"],
  "fieldCalls": [],
  "constructors": ["org.mybatis.jpetstore.domain.Account()"],
  "methods": [
    "setCountry(java.lang.String)",
    "getUsername()",
    "getPassword()",
    "setPassword(java.lang.String)",
    "equals(java.lang.Object)"
  ],
  "textAndNames": [
    "Account",
    "serialVersionUID",
    "username",
    "password",
    "email",
    "setPassword",
    "getUsername"
  ]
}
```

**Example - Mapper Interface (CategoryMapper):**
```json
{
  "isInterface": true,
  "simpleName": "CategoryMapper",
  "fullName": "org.mybatis.jpetstore.mapper.CategoryMapper",
  "fieldTypes": [],
  "parameterTypes": ["java.lang.String"],
  "returnTypes": ["java.util.List", "org.mybatis.jpetstore.domain.Category"],
  "methods": [
    "getCategoryList()",
    "getCategory(java.lang.String)"
  ]
}
```

**Data Characteristics:**
- **Total types:** 49 classes/interfaces analyzed
- **Array length:** Large (comprehensive)
- **Categories:**
  - Domain objects (Account, Product, Order, Cart, etc.)
  - Mappers (MyBatis data access layer)
  - Services (business logic)
  - Action Beans (web controllers)
  - Test classes
  - Utility/Support classes

**Usage:**
- Build type hierarchies and dependency graphs
- Understand class structure and relationships
- Extract method signatures and API contracts
- Analyze inheritance chains
- Generate code documentation
- Implement static analysis tools

---

### File B: `static_analysis_results/methodData.json`

**Purpose:** Detailed method-level analysis including invocations and dependencies.

**Format:** JSON (appears to be mostly empty in analyzed file, likely contains similar structure to typeData but with method-level granularity)

**Typical Structure (when populated):**
```typescript
interface MethodData {
  methodSignature: string;
  returnType: string;
  parameters: string[];
  invocations: string[];              // Methods this method calls
  invokedBy: string[];                // Methods that call this one
  exceptions: string[];               // Throws clauses
  accessLevel: string;                // public/private/protected
}
```

**Usage:**
- Trace method call chains
- Identify circular dependencies
- Call graph analysis
- Dead code detection
- Method-level dependency analysis

---

## 4. Structural Analysis Data

### File: `structural_data/class_interactions.parquet`

**Purpose:** Define edges and relationships between classes in a graph format.

**Format:** Apache Parquet columnar format

**Typical Schema (inferred):**
```
Columns:
  - source_class: String        // Fully qualified class name
  - target_class: String        // Fully qualified class name
  - interaction_type: String    // Type of relationship
                                // e.g., "inheritance", "composition", 
                                //       "dependency", "aggregation"
  - weight: Double/Integer      // Strength or frequency of interaction
  - frequency: Integer          // Number of times interaction occurs
```

**Example Interpretation:**
```
source_class: org.mybatis.jpetstore.domain.Order
target_class: org.mybatis.jpetstore.domain.LineItem
interaction_type: composition
weight: 1.0
frequency: 5

source_class: org.mybatis.jpetstore.service.OrderService
target_class: org.mybatis.jpetstore.mapper.OrderMapper
interaction_type: dependency
weight: 0.8
frequency: 3
```

**Data Characteristics:**
- **Format:** Apache Parquet (binary, columnar)
- **Edge types:** 
  - Inheritance (is-a)
  - Composition (has-a)
  - Dependency (uses)
  - Aggregation
  - Association
- **Directionality:** Typically directed graphs
- **Weight:** May represent coupling strength or interaction frequency

**Usage:**
- Build class dependency graphs
- Identify circular dependencies and bottlenecks
- Analyze component cohesion
- Detect tightly coupled classes
- Evaluate modularity metrics
- Visualize architecture
- Clustering and component boundary detection

---

## Integration and Usage Patterns

### Data Flow Architecture:
```
┌─────────────────────────────────────────────────────────────┐
│                    JPetStore Source Code                     │
└─────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓
    ┌────────┐  ┌────────────┐  ┌──────────┐  ┌────────────┐
    │ Dynamic│  │  Semantic  │  │  Static  │  │Structural │
    │ Analysis│  │  Analysis  │  │ Analysis │  │ Analysis  │
    └────────┘  └────────────┘  └──────────┘  └────────────┘
         ↓              ↓              ↓              ↓
    ┌────────┐  ┌────────────┐  ┌──────────┐  ┌────────────┐
    │class_  │  │class_word_ │  │typeData+ │  │class_      │
    │per_bcs │  │count.      │  │methodData│  │interactions│
    │.json   │  │parquet     │  │.json     │  │.parquet    │
    └────────┘  └────────────┘  └──────────┘  └────────────┘
```

### Combined Usage Scenarios:

**1. Component Clustering:**
- Use `class_interactions.parquet` for graph structure
- Use `typeData.json` for class metadata
- Cluster classes into cohesive microservices

**2. Semantic Similarity:**
- Use `class_word_count.parquet` for semantic vectors
- Use `typeData.json` for structural validation
- Find semantically related classes

**3. Test Impact Analysis:**
- Use `class_per_bcs.json` to find affected classes
- Use `typeData.json` for dependency analysis
- Determine regression test scope

**4. Architecture Quality:**
- Use `class_interactions.parquet` for coupling analysis
- Use `typeData.json` for inheritance depth
- Calculate modularity metrics

---

## Technical Implementation Notes

### For LLM Code Generation:

1. **When Processing typeData.json:**
   - Each array element represents one type definition
   - Access methods via array indexing and filtering by `fullName`
   - Reconstruct class hierarchy from `inheritedTypes`

2. **When Processing Parquet Files:**
   - Use pandas/polars to read: `pd.read_parquet('file.parquet')`
   - Parquet is optimized for columnar operations
   - Can filter rows efficiently by column predicates

3. **When Processing class_per_bcs.json:**
   - Treat as adjacency list for class interaction graph
   - Key is the entry point (test method)
   - Value array is the set of accessed classes

### Data Volume Estimates:
- **typeData.json:** ~49 classes, ~50KB (formatted)
- **class_per_bcs.json:** ~80+ entries, ~30KB
- **class_word_count.parquet:** Thousands of rows, ~100-500KB
- **class_interactions.parquet:** Hundreds to thousands of edges, ~50-200KB

### Query Patterns:
```python
# Reading and filtering examples

# TypeData filtering
account_class = [t for t in typeData if t['fullName'] == 'org.mybatis.jpetstore.domain.Account'][0]

# Parquet reading
import pandas as pd
interactions = pd.read_parquet('class_interactions.parquet')
service_deps = interactions[interactions['source_class'].str.contains('service')]

# Dynamic analysis lookup
bcs_results = class_per_bcs['CartTest_addItemWhenIsInStockIsTrue()']
```

---

## Microservice Decomposition Context

These data formats are specifically designed for **monolithic to microservice decomposition** research. They enable:

1. **Dependency Analysis** - Identify which classes must stay together
2. **Semantic Grouping** - Find classes with similar functionality
3. **Behavioral Slicing** - Understand class interactions through testing
4. **Architecture Evaluation** - Measure decomposition quality

The combination of static, dynamic, semantic, and structural data provides a **360-degree view** of the codebase for intelligent decomposition.

---

## References

- **Static Analysis Tool:** Likely SootUp or similar Java analysis framework
- **Semantic Analysis:** TF-IDF or word frequency-based embedding
- **Dynamic Analysis:** Test execution tracing (class_per_bcs = Class Per Behavioral Component Slice)
- **Structural Analysis:** Dependency graph representation
