"""
JPetStore-6 Data Format Python Reference Guide

This module provides helper classes and functions to parse and understand
the JPetStore-6 analysis data formats for LLM-based code generation.
"""

from typing import List, Dict, Any, Optional
import json
import pandas as pd
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# DATA MODELS
# ============================================================================

class InteractionType(Enum):
    """Types of class interactions in structural data"""
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    DEPENDENCY = "dependency"
    AGGREGATION = "aggregation"
    ASSOCIATION = "association"
    METHOD_CALL = "method_call"


@dataclass
class TypeInfo:
    """Represents a Java type from typeData.json"""
    is_interface: bool
    is_annotation: bool
    is_anonymous: bool
    simple_name: str
    full_name: str
    referenced_types: List[str]
    field_types: List[str]
    parameter_types: List[str]
    return_types: List[str]
    inherited_types: List[str]
    constructors: List[str]
    methods: List[str]
    nested_types: List[str] = None
    field_calls: List[Dict[str, Any]] = None
    text_and_names: List[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TypeInfo':
        """Convert JSON object to TypeInfo"""
        return cls(
            is_interface=data.get('isInterface', False),
            is_annotation=data.get('isAnnotation', False),
            is_anonymous=data.get('isAnonymous', False),
            simple_name=data.get('simpleName', ''),
            full_name=data.get('fullName', ''),
            referenced_types=data.get('referencedTypes', []),
            field_types=data.get('fieldTypes', []),
            parameter_types=data.get('parameterTypes', []),
            return_types=data.get('returnTypes', []),
            inherited_types=data.get('inheritedTypes', []),
            constructors=data.get('constructors', []),
            methods=data.get('methods', []),
            nested_types=data.get('nestedTypes', []),
            field_calls=data.get('fieldCalls', []),
            text_and_names=data.get('textAndNames', [])
        )
    
    def get_dependencies(self) -> List[str]:
        """Get all class dependencies"""
        deps = set(self.referenced_types) - {self.full_name}
        deps.update(self.inherited_types)
        deps.update(self.field_types)
        deps.update(self.parameter_types)
        deps.update(self.return_types)
        return list(deps)
    
    def is_domain_class(self) -> bool:
        """Check if this is a domain model class"""
        return ('domain' in self.full_name and 
                not self.is_interface and 
                not self.full_name.endswith('Test'))
    
    def is_mapper(self) -> bool:
        """Check if this is a MyBatis mapper interface"""
        return 'mapper' in self.full_name and self.is_interface
    
    def is_service(self) -> bool:
        """Check if this is a service class"""
        return 'service' in self.full_name and not self.is_interface
    
    def is_action_bean(self) -> bool:
        """Check if this is a web action bean"""
        return 'actions' in self.full_name


@dataclass
class ClassInteraction:
    """Represents an edge in the class interaction graph"""
    source_class: str
    target_class: str
    interaction_type: InteractionType
    weight: float = 1.0
    frequency: int = 1
    
    def __hash__(self):
        return hash((self.source_class, self.target_class))
    
    def __eq__(self, other):
        if not isinstance(other, ClassInteraction):
            return False
        return (self.source_class == other.source_class and 
                self.target_class == other.target_class)


# ============================================================================
# DATA LOADERS
# ============================================================================

class DataLoader:
    """Loads and caches JPetStore analysis data"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self._type_data_cache: Optional[List[TypeInfo]] = None
        self._class_per_bcs_cache: Optional[Dict[str, List[str]]] = None
        self._interactions_cache: Optional[pd.DataFrame] = None
        self._word_count_cache: Optional[pd.DataFrame] = None
    
    def load_type_data(self) -> List[TypeInfo]:
        """Load and parse typeData.json"""
        if self._type_data_cache is not None:
            return self._type_data_cache
        
        path = f"{self.base_path}/static_analysis_results/typeData.json"
        with open(path, 'r') as f:
            raw_data = json.load(f)
        
        self._type_data_cache = [TypeInfo.from_dict(item) for item in raw_data]
        return self._type_data_cache
    
    def load_class_per_bcs(self) -> Dict[str, List[str]]:
        """Load class_per_bcs.json (dynamic analysis)"""
        if self._class_per_bcs_cache is not None:
            return self._class_per_bcs_cache
        
        path = f"{self.base_path}/dynamic_analysis/class_per_bcs.json"
        with open(path, 'r') as f:
            self._class_per_bcs_cache = json.load(f)
        
        return self._class_per_bcs_cache
    
    def load_class_interactions(self) -> pd.DataFrame:
        """Load class_interactions.parquet (structural data)"""
        if self._interactions_cache is not None:
            return self._interactions_cache
        
        path = f"{self.base_path}/structural_data/class_interactions.parquet"
        self._interactions_cache = pd.read_parquet(path)
        return self._interactions_cache
    
    def load_word_counts(self) -> pd.DataFrame:
        """Load class_word_count.parquet (semantic data)"""
        if self._word_count_cache is not None:
            return self._word_count_cache
        
        path = f"{self.base_path}/semantic_data/class_word_count.parquet"
        self._word_count_cache = pd.read_parquet(path)
        return self._word_count_cache


# ============================================================================
# QUERY INTERFACES
# ============================================================================

class TypeDataQuery:
    """Query interface for typeData"""
    
    def __init__(self, types: List[TypeInfo]):
        self.types = types
        self._by_full_name = {t.full_name: t for t in types}
        self._by_simple_name = {t.simple_name: [t for t in types if t.simple_name == t.simple_name] 
                                for t in types}
    
    def find_by_full_name(self, full_name: str) -> Optional[TypeInfo]:
        """Find a type by its fully qualified name"""
        return self._by_full_name.get(full_name)
    
    def find_by_simple_name(self, simple_name: str) -> List[TypeInfo]:
        """Find all types with a given simple name"""
        return [t for t in self.types if t.simple_name == simple_name]
    
    def get_domain_classes(self) -> List[TypeInfo]:
        """Get all domain model classes"""
        return [t for t in self.types if t.is_domain_class()]
    
    def get_mappers(self) -> List[TypeInfo]:
        """Get all mapper interfaces"""
        return [t for t in self.types if t.is_mapper()]
    
    def get_services(self) -> List[TypeInfo]:
        """Get all service classes"""
        return [t for t in self.types if t.is_service()]
    
    def get_action_beans(self) -> List[TypeInfo]:
        """Get all action beans (web controllers)"""
        return [t for t in self.types if t.is_action_bean()]
    
    def get_test_classes(self) -> List[TypeInfo]:
        """Get all test classes"""
        return [t for t in self.types if 'Test' in t.simple_name]
    
    def get_dependencies_of(self, full_name: str) -> List[TypeInfo]:
        """Get all direct dependencies of a class"""
        type_info = self.find_by_full_name(full_name)
        if not type_info:
            return []
        
        deps = type_info.get_dependencies()
        result = []
        for dep_name in deps:
            dep_type = self.find_by_full_name(dep_name)
            if dep_type:
                result.append(dep_type)
        
        return result
    
    def get_dependents_of(self, full_name: str) -> List[TypeInfo]:
        """Get all classes that depend on this class"""
        dependents = []
        for type_info in self.types:
            if full_name in type_info.get_dependencies():
                dependents.append(type_info)
        return dependents


class DynamicAnalysisQuery:
    """Query interface for class_per_bcs data"""
    
    def __init__(self, bcs_data: Dict[str, List[str]]):
        self.bcs_data = bcs_data
    
    def get_classes_accessed_in(self, method_name: str) -> List[str]:
        """Get all classes accessed by a specific method"""
        return self.bcs_data.get(method_name, [])
    
    def find_methods_accessing_class(self, class_name: str) -> List[str]:
        """Find all methods that access a specific class"""
        result = []
        for method, classes in self.bcs_data.items():
            if class_name in classes:
                result.append(method)
        return result
    
    def get_test_methods(self) -> List[str]:
        """Get all test method entries"""
        return [k for k in self.bcs_data.keys() if 'Test' in k]
    
    def get_accessed_classes_for_test_case(self, test_name: str) -> List[str]:
        """Get classes accessed during a specific test"""
        # Handle various test name formats
        matching_keys = [k for k in self.bcs_data.keys() 
                        if test_name in k]
        
        classes = set()
        for key in matching_keys:
            classes.update(self.bcs_data[key])
        
        return list(classes)


class StructuralAnalysisQuery:
    """Query interface for class_interactions"""
    
    def __init__(self, interactions_df: pd.DataFrame):
        self.df = interactions_df
    
    def get_dependents(self, target_class: str) -> pd.DataFrame:
        """Get all classes that depend on target_class"""
        return self.df[self.df['target_class'] == target_class]
    
    def get_dependencies(self, source_class: str) -> pd.DataFrame:
        """Get all classes that source_class depends on"""
        return self.df[self.df['source_class'] == source_class]
    
    def get_interaction_strength(self, source: str, target: str) -> float:
        """Get the weight/strength of interaction"""
        matches = self.df[(self.df['source_class'] == source) & 
                         (self.df['target_class'] == target)]
        if matches.empty:
            return 0.0
        return matches.iloc[0].get('weight', 1.0)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependency chains"""
        # Build adjacency list
        adjacency = {}
        for _, row in self.df.iterrows():
            src = row['source_class']
            tgt = row['target_class']
            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append(tgt)
        
        # DFS to find cycles (simplified)
        cycles = []
        visited = set()
        
        def dfs(node, path, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path, rec_stack)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            path.pop()
            rec_stack.remove(node)
        
        for node in adjacency.keys():
            if node not in visited:
                dfs(node, [], set())
        
        return cycles
    
    def get_isolated_classes(self) -> List[str]:
        """Find classes with no dependencies and no dependents"""
        all_classes = set(self.df['source_class']) | set(self.df['target_class'])
        connected = set(self.df['source_class']) | set(self.df['target_class'])
        return list(all_classes - connected)


class SemanticAnalysisQuery:
    """Query interface for semantic word counts"""
    
    def __init__(self, word_count_df: pd.DataFrame):
        self.df = word_count_df
    
    def get_class_vocabulary(self, class_name: str) -> Dict[str, int]:
        """Get all words and their frequencies for a class"""
        class_data = self.df[self.df['class_name'] == class_name]
        
        if class_data.empty:
            return {}
        
        # Assuming columns are 'word' and 'count'
        result = {}
        for _, row in class_data.iterrows():
            result[row['word']] = row['count']
        
        return result
    
    def find_semantically_similar_classes(self, class_name: str, 
                                         top_k: int = 5) -> List[tuple]:
        """Find classes with similar vocabulary (simple Jaccard similarity)"""
        vocab1 = self.get_class_vocabulary(class_name)
        
        if not vocab1:
            return []
        
        all_classes = self.df['class_name'].unique()
        similarities = []
        
        for other_class in all_classes:
            if other_class == class_name:
                continue
            
            vocab2 = self.get_class_vocabulary(other_class)
            
            # Jaccard similarity
            set1 = set(vocab1.keys())
            set2 = set(vocab2.keys())
            
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            
            if union > 0:
                similarity = intersection / union
                similarities.append((other_class, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_top_words_in_class(self, class_name: str, top_k: int = 10) -> List[tuple]:
        """Get the most frequent words in a class"""
        vocab = self.get_class_vocabulary(class_name)
        
        words_sorted = sorted(vocab.items(), key=lambda x: x[1], reverse=True)
        return words_sorted[:top_k]


# ============================================================================
# ANALYSIS UTILITIES
# ============================================================================

class ComponentAnalyzer:
    """Analyze and identify components for decomposition"""
    
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.type_query = None
        self.structural_query = None
        self.dynamic_query = None
        self.semantic_query = None
        self._initialize()
    
    def _initialize(self):
        """Initialize all query interfaces"""
        types = self.loader.load_type_data()
        self.type_query = TypeDataQuery(types)
        
        interactions = self.loader.load_class_interactions()
        self.structural_query = StructuralAnalysisQuery(interactions)
        
        bcs = self.loader.load_class_per_bcs()
        self.dynamic_query = DynamicAnalysisQuery(bcs)
        
        word_counts = self.loader.load_word_counts()
        self.semantic_query = SemanticAnalysisQuery(word_counts)
    
    def identify_cohesive_components(self) -> Dict[str, List[str]]:
        """Identify highly cohesive class clusters"""
        components = {}
        
        # Group by package
        types_by_package = {}
        for type_info in self.type_query.types:
            package = type_info.full_name.rsplit('.', 1)[0]
            if package not in types_by_package:
                types_by_package[package] = []
            types_by_package[package].append(type_info.full_name)
        
        return types_by_package
    
    def get_high_coupling_classes(self, threshold: int = 3) -> List[str]:
        """Find classes with high coupling (many dependencies)"""
        coupling_count = {}
        
        for type_info in self.type_query.types:
            deps = len(type_info.get_dependencies())
            if deps >= threshold:
                coupling_count[type_info.full_name] = deps
        
        # Sort by coupling count
        return sorted(coupling_count.keys(), 
                     key=lambda x: coupling_count[x], 
                     reverse=True)
    
    def trace_test_to_components(self, test_name: str) -> Dict[str, List[str]]:
        """Trace which components a test accesses"""
        classes = self.dynamic_query.get_accessed_classes_for_test_case(test_name)
        
        components = {}
        for class_name in classes:
            package = class_name.rsplit('.', 1)[0]
            if package not in components:
                components[package] = []
            components[package].append(class_name)
        
        return components


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example usage
    base_path = "/path/to/jpetstore-6"
    loader = DataLoader(base_path)
    
    # Load all data
    types = loader.load_type_data()
    bcs_data = loader.load_class_per_bcs()
    interactions = loader.load_class_interactions()
    word_counts = loader.load_word_counts()
    
    # Create query interfaces
    type_query = TypeDataQuery(types)
    dynamic_query = DynamicAnalysisQuery(bcs_data)
    
    # Example queries
    account_type = type_query.find_by_full_name(
        "org.mybatis.jpetstore.domain.Account"
    )
    if account_type:
        print(f"Account class methods: {account_type.methods}")
    
    services = type_query.get_services()
    print(f"Services found: {len(services)}")
    
    # Analyzer usage
    analyzer = ComponentAnalyzer(loader)
    high_coupling = analyzer.get_high_coupling_classes()
    print(f"High coupling classes: {high_coupling}")
