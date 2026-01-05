# JPetStore-6 Data Flow & Integration Guide

## Data Transformation Pipeline

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Source Code (JPetStore)                            │
└────────────────────────────────────────────────────────────────────────────┘
                    │
                    ├──────────────────┬──────────────────┬──────────────────┐
                    ↓                  ↓                  ↓                  ↓
        ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐
        │ Static Analysis  │  │ Dynamic Analysis │  │ Semantic Anal. │  │Structural    │
        │  (AST-based)     │  │  (Runtime trace) │  │   (NLP/ML)     │  │  (Graph)     │
        └──────────────────┘  └──────────────────┘  └────────────────┘  └──────────────┘
                    │                  │                  │                  │
                    ├──────────────────┼──────────────────┼──────────────────┤
                    ↓                  ↓                  ↓                  ↓
        ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐
        │ typeData.json    │  │class_per_bcs.    │  │class_word_     │  │class_        │
        │ methodData.json  │  │json              │  │count.parquet   │  │interactions  │
        │                  │  │                  │  │                │  │.parquet      │
        │ Structure Info   │  │ BCS Mapping      │  │ Vocabulary     │  │ Dependencies │
        │ Type Hierarchy   │  │ Test→Classes     │  │ Frequencies    │  │ Relationships│
        │ Method Sigs      │  │ Runtime Trace    │  │ Embeddings     │  │ Graph Edges  │
        └──────────────────┘  └──────────────────┘  └────────────────┘  └──────────────┘
                    │                  │                  │                  │
                    └──────────────────┼──────────────────┼──────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ↓                                     ↓
        ┌─────────────────────────────────┐  ┌─────────────────────────────┐
        │  Decomposition Analysis Tools   │  │  LLM Code Generation Tools  │
        │                                 │  │                             │
        │ • Component Clustering          │  │ • Service Design            │
        │ • Dependency Graph Analysis     │  │ • API Contract Generation   │
        │ • Cohesion/Coupling Metrics     │  │ • Microservice Scaffolding  │
        │ • Architectural Patterns        │  │ • Configuration Generation  │
        │ • Circular Dependency Detection │  │ • Test Case Generation      │
        └─────────────────────────────────┘  └─────────────────────────────┘
```

---

## Data Relationships & Cross-References

```
typeData.json
├─ Account (TypeInfo)
│  ├─ fullName: "org.mybatis.jpetstore.domain.Account"
│  ├─ methods: [getUsername(), setPassword(...), ...]
│  ├─ fieldTypes: [long, String, String, ...]
│  ├─ referencedTypes: [String, Validate, Account, ...]
│  └─ inheritedTypes: [Serializable]
│
├─ (Cross-ref to) class_per_bcs.json
│  └─ "AccountActionBeanTest_getUsernameOutputNull()"
│     └─ [AccountActionBeanTest, AccountActionBean, Account]
│
├─ (Cross-ref to) class_interactions.parquet
│  └─ AccountService → Account (dependency)
│  └─ Account ← (inherited by) many classes
│
└─ (Cross-ref to) class_word_count.parquet
   └─ word: "password", count: 5
   └─ word: "username", count: 7


class_per_bcs.json (Dynamic)
├─ Key: "CartTest_addItemWhenIsInStockIsTrue()"
├─ Value: [CartTest, Item, Cart, CartItem]
│
├─ (Cross-ref to) typeData.json
│  ├─ CartTest.methods contains addItemWhenIsInStockIsTrue()
│  ├─ Item.fieldTypes includes "String itemId"
│  ├─ Cart.methods contains addItem(Item, boolean)
│  └─ CartItem.fieldTypes includes "Item item"
│
├─ (Cross-ref to) class_interactions.parquet
│  ├─ Cart → CartItem (composition)
│  ├─ Cart → Item (dependency)
│  └─ CartItem → Item (dependency)
│
└─ Insight: This test exercises the cart composition pattern


class_interactions.parquet (Structural)
├─ Edge: Order → LineItem (composition, weight=1.0, freq=5)
├─ Edge: Order → Account (dependency, weight=0.8, freq=3)
├─ Edge: OrderService → OrderMapper (dependency, weight=0.9, freq=4)
│
├─ (Cross-ref to) typeData.json
│  ├─ Order.fieldTypes: [List<LineItem>, Account, ...]
│  ├─ LineItem.fieldTypes: [Item, int quantity, ...]
│  └─ OrderService.methods: [insertOrder(Order), getOrder(int), ...]
│
├─ (Cross-ref to) class_per_bcs.json
│  └─ "OrderServiceTest_shouldCallTheMapperToInsert()"
│     └─ Tests all three classes: Order, LineItem, OrderMapper
│
└─ (Cross-ref to) class_word_count.parquet
   └─ Order: {order:10, items:8, payment:6, shipping:7, ...}
   └─ LineItem: {item:12, quantity:5, price:4, ...}


class_word_count.parquet (Semantic)
├─ Account: {password:5, username:7, email:3, address:4, ...}
├─ Order: {order:10, items:8, payment:6, shipping:7, ...}
├─ LineItem: {item:12, quantity:5, price:4, unit:3, ...}
│
├─ (Similarity analysis)
│  └─ Order & LineItem similarity: high (both mention items, price)
│  └─ Account & Order similarity: low (different domains)
│
└─ (Cross-ref to) class_interactions.parquet
   └─ High semantic similarity often correlates with structural dependency
```

---

## Data Flow For Different Queries

### Query: "Design a microservice for order processing"

```
Step 1: Identify Core Classes (typeData)
  ↓
  Classes: Order, LineItem, OrderService, OrderMapper, OrderActionBean

Step 2: Find Dependencies (typeData + class_interactions)
  ↓
  Order depends on: LineItem, Account, Item
  OrderService depends on: OrderMapper, SequenceMapper, LineItemMapper, ItemMapper
  
Step 3: Identify Behavioral Slices (class_per_bcs)
  ↓
  Tests show: OrderServiceTest uses Order, LineItem, Sequence, OrderMapper
  OrderActionBeanTest uses OrderActionBean, Order, OrderService

Step 4: Analyze Coupling (class_interactions)
  ↓
  Internal cohesion (Order ↔ LineItem): HIGH
  External coupling (OrderService ↔ ItemMapper): MEDIUM
  
Step 5: Generate Microservice Boundary
  ↓
  Core: Order, LineItem, OrderService, OrderMapper, LineItemMapper
  Boundary: ItemMapper (can be external service)
  Communication: REST for Item lookups
```

### Query: "Find semantically similar classes"

```
Step 1: Get vocabulary for a class (class_word_count)
  ↓
  Order vocabulary: {order, item, customer, payment, shipping, ...}

Step 2: Compare with other classes
  ↓
  Order & Cart vocabulary similarity: HIGH (both have items)
  Order & Account vocabulary similarity: LOW (different aspects)

Step 3: Validate with structural relationships (class_interactions)
  ↓
  Order & Cart in same package? YES
  Order → Cart dependency? NO (but both → Item)
  
Step 4: Check dynamic relationships (class_per_bcs)
  ↓
  Both tested in shopping flow? YES
  Same test cases? NO (different responsibilities)
```

### Query: "Identify test coverage gaps"

```
Step 1: Get all tested classes (class_per_bcs)
  ↓
  Tested: {Account, Order, Cart, CartItem, ...}

Step 2: Get all classes in codebase (typeData)
  ↓
  Total: {Account, Order, Product, ..., 49 classes}

Step 3: Find untested classes
  ↓
  Not tested: {Sequence, Category, SequenceMapper, ...}

Step 4: Analyze dependencies of untested (typeData)
  ↓
  If untested class is depended upon by tested classes,
  there's indirect testing through integration

Step 5: Prioritize (class_interactions)
  ↓
  High coupling untested class = HIGH PRIORITY
  Low coupling untested class = LOW PRIORITY
```

---

## Layer-Based Data Integration

```
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (web.actions)                                │
│ ActionBeans: AccountActionBean, OrderActionBean, CartActionBean │
│                                                                  │
│ Data from: typeData, class_per_bcs (test flow)                  │
│ Interactions: → Service classes                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (class_interactions)
┌─────────────────────────────────────────────────────────────────┐
│ BUSINESS LOGIC LAYER (service)                                  │
│ Services: AccountService, OrderService, CatalogService          │
│                                                                  │
│ Data from: typeData, class_per_bcs (test scenarios)             │
│ Interactions: ↑ from ActionBeans, ↓ to Mappers                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (class_interactions)
┌─────────────────────────────────────────────────────────────────┐
│ DATA ACCESS LAYER (mapper)                                      │
│ Mappers: AccountMapper, OrderMapper, ItemMapper, etc.           │
│                                                                  │
│ Data from: typeData (interfaces)                                │
│ Interactions: ↑ from Services, ↓ to Domain                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓ (class_interactions)
┌─────────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (domain)                                           │
│ Entities: Account, Order, Product, Cart, LineItem, etc.         │
│                                                                  │
│ Data from: typeData, class_word_count (semantics)               │
│ Interactions: Composition, Aggregation within domain            │
│                                                                  │
│ Key Relationships:                                              │
│ • Order composition → LineItem (1:many)                         │
│ • Cart composition → CartItem (1:many)                          │
│ • Order dependency → Account (reference)                        │
│ • LineItem dependency → Item (reference)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Query Execution Patterns

### Pattern 1: Type-Centric (Start from typeData)

```
Input: Class name
  ↓
Find TypeInfo in typeData
  ↓
Extract methods, fields, dependencies
  ↓
Find interactions in class_interactions
  ↓
Find tests in class_per_bcs
  ↓
Find semantic info in class_word_count
  ↓
Output: Complete class profile
```

### Pattern 2: Dependency-Centric (Start from class_interactions)

```
Input: Source and Target classes
  ↓
Find edge in class_interactions
  ↓
Get interaction type and weight
  ↓
Look up both TypeInfo in typeData
  ↓
Find tests using both in class_per_bcs
  ↓
Compare semantics in class_word_count
  ↓
Output: Relationship analysis
```

### Pattern 3: Test-Centric (Start from class_per_bcs)

```
Input: Test method name
  ↓
Find classes in class_per_bcs
  ↓
Look up each in typeData
  ↓
Get their interactions from class_interactions
  ↓
Extract their methods and signatures
  ↓
Find semantic overlap in class_word_count
  ↓
Output: Test scenario understanding
```

### Pattern 4: Semantic-Centric (Start from class_word_count)

```
Input: Keyword or class name
  ↓
Find similar classes by vocabulary
  ↓
Look up classes in typeData
  ↓
Check structural relationships in class_interactions
  ↓
Verify with dynamic tests in class_per_bcs
  ↓
Output: Semantic component groups
```

---

## Data Quality & Completeness

```
Data Source              Coverage              Completeness
─────────────────────────────────────────────────────────────
typeData.json            All 49 classes        Complete type info
                         All methods           All signatures
                         All fields            All declarations

class_per_bcs.json       ~80 test methods      All test executions
                         Classes accessed      Runtime snapshot
                         Multiple per class    During testing

class_word_count.parquet All classes           Semantic vectors
                         1000+ word entries    Vocabulary coverage
                         Frequency counts      Relative importance

class_interactions.      100-500 edges         Structural graph
parquet                  Multiple types        All relationships
                         Weight/frequency      Coupling strength
```

---

## Integration Checklist for LLM Processing

```
□ Load all four data sources
  ├─ typeData.json        (JSON parse)
  ├─ class_per_bcs.json   (JSON parse)
  ├─ class_word_count     (Parquet read)
  └─ class_interactions   (Parquet read)

□ Index by primary keys
  ├─ typeData by fullName → O(1) lookup
  ├─ class_per_bcs by method name → O(1) lookup
  ├─ interactions by (source, target) → O(1) lookup
  └─ word_count by (class, word) → O(1) lookup

□ Build in-memory indexes
  ├─ Class → Methods mapping
  ├─ Class → Dependencies mapping
  ├─ Class → Dependents mapping
  ├─ Test → Accessed Classes mapping
  └─ Word → Classes containing it mapping

□ Validate cross-references
  ├─ All classes in class_interactions exist in typeData
  ├─ All classes in class_per_bcs exist in typeData
  ├─ All methods in class_per_bcs correspond to tests in typeData
  └─ No circular references that indicate data errors

□ Compute derived metrics
  ├─ Coupling scores per class
  ├─ Cohesion scores per package
  ├─ Test coverage percentage
  ├─ Semantic similarity matrix
  └─ Architectural metrics

□ Prepare for output
  ├─ Format for LLM prompt (structured text)
  ├─ Provide query examples
  ├─ Include context about JPetStore structure
  └─ Suggest decomposition boundaries
```

---

## Performance Tips

```
For Quick Lookups:
• Create index dicts for typeData by fullName
• Pre-compute common queries (dependencies, dependents)
• Cache parsed Parquet DataFrames

For Complex Analysis:
• Use pandas for columnar operations
• Filter early (row filtering before joins)
• Use set operations instead of loops

For LLM Integration:
• Serialize results as JSON
• Include relevant context automatically
• Batch queries when possible
• Cache frequently accessed classes
```

---

## Common Mistakes to Avoid

```
❌ Not filtering out java.* classes when analyzing dependencies
   ✓ Only count application classes

❌ Treating interfaces same as implementations
   ✓ Check isInterface flag in typeData

❌ Ignoring composition vs. dependency relationships
   ✓ Use interaction_type in class_interactions

❌ Not normalizing class names in cross-file queries
   ✓ Always use fully qualified names

❌ Assuming absence in class_per_bcs means untested
   ✓ May be tested indirectly through integration tests

❌ Not deduplicating word_count entries
   ✓ Aggregate by class before similarity analysis
```
