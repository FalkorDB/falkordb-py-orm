# Phase 3 Quick Implementation Guide

This is a quick reference for implementing each sub-phase of Phase 3.

## Phase 3a: Relationship Metadata & Declaration

### Step 1: Extend metadata.py
```python
# Add to metadata.py

@dataclass
class RelationshipMetadata:
    """Metadata for a relationship between entities."""
    relationship_name: str          # Python attribute name
    relationship_type: str           # Cypher edge type (e.g., "KNOWS")
    direction: str                   # "OUTGOING", "INCOMING", "BOTH"
    target_class: Optional[Type]     # Resolved target class
    target_class_name: str           # For forward references
    is_collection: bool              # List[T] vs Optional[T]
    lazy: bool = True                # Lazy load by default
    cascade: bool = False            # Don't cascade by default

# Add to EntityMetadata
@dataclass
class EntityMetadata:
    # ... existing fields ...
    relationships: List[RelationshipMetadata] = field(default_factory=list)
    
    def get_relationship(self, name: str) -> Optional[RelationshipMetadata]:
        for rel in self.relationships:
            if rel.relationship_name == name:
                return rel
        return None
```

### Step 2: Add relationship descriptor to decorators.py
```python
# Add to decorators.py

class RelationshipDescriptor:
    """Descriptor for relationship mapping."""
    def __init__(self, type: str, direction: str, target: Type, lazy: bool, cascade: bool):
        self.relationship_type = type
        self.direction = direction
        self.target = target
        self.lazy = lazy
        self.cascade = cascade
        self._python_name: Optional[str] = None
        
    def __set_name__(self, owner: Type, name: str) -> None:
        self._python_name = name
    
    def __get__(self, instance: Any, owner: Type) -> Any:
        if instance is None:
            return self
        return getattr(instance, f"_{self._python_name}", None)
    
    def __set__(self, instance: Any, value: Any) -> None:
        setattr(instance, f"_{self._python_name}", value)

def relationship(
    type: str,
    direction: str = "OUTGOING",
    target: Type = None,
    lazy: bool = True,
    cascade: bool = False
) -> Any:
    """Define a relationship to another entity."""
    return RelationshipDescriptor(type, direction, target, lazy, cascade)
```

### Step 3: Update @node decorator
```python
# Modify @node decorator in decorators.py to detect relationships
# In the decorator function, after scanning properties:

# Scan for relationships
for attr_name, attr_value in inspect.getmembers(cls):
    if isinstance(attr_value, RelationshipDescriptor):
        # Get type hint to determine target class
        target_type = type_hints.get(attr_name, Any)
        
        # Check if it's a collection
        is_collection = False
        target_class_name = None
        
        # Handle List[T], Optional[T], etc.
        if hasattr(target_type, '__origin__'):
            if target_type.__origin__ is list:
                is_collection = True
                target_class_name = str(target_type.__args__[0])
            elif target_type.__origin__ is Union:  # Optional
                target_class_name = str(target_type.__args__[0])
        
        rel_meta = RelationshipMetadata(
            relationship_name=attr_name,
            relationship_type=attr_value.relationship_type,
            direction=attr_value.direction,
            target_class=attr_value.target,
            target_class_name=target_class_name or str(target_type),
            is_collection=is_collection,
            lazy=attr_value.lazy,
            cascade=attr_value.cascade
        )
        metadata.relationships.append(rel_meta)
```

### Step 4: Create tests
```python
# tests/test_relationship_metadata.py

def test_declare_one_to_many():
    @node("Person")
    class Person:
        id: Optional[int] = None
        friends: List["Person"] = relationship(type="KNOWS")
    
    metadata = get_entity_metadata(Person)
    assert len(metadata.relationships) == 1
    assert metadata.relationships[0].relationship_name == "friends"
    assert metadata.relationships[0].is_collection is True

def test_declare_many_to_one():
    @node("Person")
    class Person:
        id: Optional[int] = None
        company: Optional["Company"] = relationship(type="WORKS_FOR")
    
    metadata = get_entity_metadata(Person)
    assert len(metadata.relationships) == 1
    assert metadata.relationships[0].is_collection is False
```

---

## Phase 3b: Lazy Loading System

### Step 1: Create LazyList in relationships.py
```python
# Create new file: falkordb_orm/relationships.py

class LazyList:
    """Proxy for lazy-loaded list of entities."""
    def __init__(self, graph, source_id, rel_metadata, mapper, query_builder):
        self._graph = graph
        self._source_id = source_id
        self._rel_metadata = rel_metadata
        self._mapper = mapper
        self._query_builder = query_builder
        self._loaded = False
        self._items: List = []
    
    def _load(self):
        if self._loaded:
            return
        
        # Build and execute query
        cypher, params = self._query_builder.build_relationship_load_query(
            self._rel_metadata, self._source_id
        )
        result = self._graph.query(cypher, params)
        
        # Map results to entities
        for record in result.result_set:
            entity = self._mapper.map_from_record(
                record, self._rel_metadata.target_class
            )
            self._items.append(entity)
        
        self._loaded = True
    
    def __iter__(self):
        self._load()
        return iter(self._items)
    
    def __len__(self):
        self._load()
        return len(self._items)
```

### Step 2: Extend query_builder.py
```python
# Add to QueryBuilder class

def build_relationship_load_query(
    self, rel_metadata: RelationshipMetadata, source_id: Any
) -> tuple[str, Dict[str, Any]]:
    """Build query to load relationship."""
    # Determine arrow direction
    if rel_metadata.direction == "OUTGOING":
        arrow = "-[:%s]->" % rel_metadata.relationship_type
    elif rel_metadata.direction == "INCOMING":
        arrow = "<-[:%s]-" % rel_metadata.relationship_type
    else:  # BOTH
        arrow = "-[:%s]-" % rel_metadata.relationship_type
    
    # Resolve target label (simplified - may need more logic)
    target_label = rel_metadata.target_class_name.strip('"\'')
    
    cypher = f"MATCH (source){arrow}(target:{target_label}) WHERE id(source) = $source_id RETURN target"
    params = {"source_id": source_id}
    
    return cypher, params
```

### Step 3: Extend mapper.py
```python
# Add to EntityMapper class

def _initialize_lazy_relationships(self, entity: Any, entity_id: int):
    """Initialize lazy relationship proxies."""
    metadata = self.get_entity_metadata(type(entity))
    
    for rel_meta in metadata.relationships:
        if rel_meta.lazy:
            if rel_meta.is_collection:
                proxy = LazyList(
                    self._graph, entity_id, rel_meta, self, self._query_builder
                )
            else:
                proxy = LazySingle(
                    self._graph, entity_id, rel_meta, self, self._query_builder
                )
            setattr(entity, rel_meta.relationship_name, proxy)

# Modify map_from_node to call _initialize_lazy_relationships
def map_from_node(self, node: Any, entity_class: Type[T]) -> T:
    # ... existing code ...
    entity = entity_class(**kwargs)
    
    # Initialize lazy relationships if entity has ID
    if internal_id is not None:
        self._initialize_lazy_relationships(entity, internal_id)
    
    return entity
```

---

## Phase 3c: Cascade Operations

### Step 1: Create RelationshipManager
```python
# Add to relationships.py

class RelationshipManager:
    """Manages relationship persistence."""
    def __init__(self, graph, mapper, query_builder):
        self._graph = graph
        self._mapper = mapper
        self._query_builder = query_builder
        self._entity_tracker: Set[int] = set()
    
    def save_relationships(self, entity: Any):
        """Save all relationships for an entity."""
        metadata = self._mapper.get_entity_metadata(type(entity))
        entity_id = self._get_entity_id(entity, metadata)
        
        for rel_meta in metadata.relationships:
            related = getattr(entity, rel_meta.relationship_name, None)
            
            if related is None:
                continue
            
            # Handle collection vs single
            if rel_meta.is_collection:
                for related_entity in related:
                    self._save_single_relationship(
                        entity_id, related_entity, rel_meta
                    )
            else:
                self._save_single_relationship(
                    entity_id, related, rel_meta
                )
    
    def _save_single_relationship(self, source_id, target_entity, rel_meta):
        """Save a single relationship."""
        # Get or save target entity
        target_id = self._get_or_save_entity(target_entity, rel_meta)
        
        # Create edge
        cypher, params = self._query_builder.build_relationship_create_query(
            source_id, target_id, rel_meta
        )
        self._graph.query(cypher, params)
```

---

## Phase 3d: Eager Loading

### Step 1: Add fetch parameter to Repository
```python
# Modify find_by_id in repository.py

def find_by_id(self, entity_id: Any, fetch: Optional[List[str]] = None) -> Optional[T]:
    """Find entity by ID with optional eager loading."""
    if fetch:
        # Use eager loading
        return self._find_with_eager_loading(entity_id, fetch)
    
    # Use existing lazy loading
    # ... existing code ...
```

### Step 2: Build eager loading query
```python
# Add to QueryBuilder

def build_eager_loading_query(
    self, metadata: EntityMetadata, entity_id: Any, fetch_hints: List[str]
) -> tuple[str, Dict[str, Any]]:
    """Build query with OPTIONAL MATCH for relationships."""
    labels = ':'.join(metadata.labels)
    cypher = f"MATCH (p:{labels}) WHERE id(p) = $id\n"
    
    # Add OPTIONAL MATCH for each fetch hint
    for hint in fetch_hints:
        rel_meta = metadata.get_relationship(hint)
        if rel_meta:
            arrow = self._get_arrow(rel_meta.direction, rel_meta.relationship_type)
            target_label = rel_meta.target_class_name.strip('"\'')
            cypher += f"OPTIONAL MATCH (p){arrow}({hint}:{target_label})\n"
    
    # Build return clause
    return_parts = ["p"] + [f"collect(DISTINCT {hint}) as {hint}" for hint in fetch_hints]
    cypher += "RETURN " + ", ".join(return_parts)
    
    return cypher, {"id": entity_id}
```

---

## Testing Checklist

### Phase 3a Tests
- [ ] Can declare relationship with decorator
- [ ] Metadata extracted correctly
- [ ] Forward references work
- [ ] List vs Optional detected
- [ ] Direction stored correctly

### Phase 3b Tests
- [ ] LazyList loads on iteration
- [ ] LazySingle loads on access
- [ ] Second access uses cache
- [ ] Empty relationships work
- [ ] Correct queries generated

### Phase 3c Tests
- [ ] Cascade saves related entities
- [ ] Non-cascade skips saves
- [ ] Edges created correctly
- [ ] Circular refs handled
- [ ] Bidirectional works

### Phase 3d Tests
- [ ] Fetch loads relationships
- [ ] No additional queries
- [ ] Multiple fetch hints work
- [ ] Performance improved

---

## Common Patterns

### Resolving Forward References
```python
def resolve_target_class(type_hint_str: str, module_globals: dict) -> Type:
    """Resolve forward reference to actual class."""
    # Strip quotes
    class_name = type_hint_str.strip('"\'')
    
    # Try to get from globals
    if class_name in module_globals:
        return module_globals[class_name]
    
    # Return None if not found - will be resolved later
    return None
```

### Tracking Entities During Save
```python
def _get_or_save_entity(self, entity, rel_meta):
    """Get entity ID or save if cascade."""
    # Check if entity has ID
    entity_id = getattr(entity, 'id', None)
    
    if entity_id is not None:
        return entity_id
    
    # Check if cascade
    if not rel_meta.cascade:
        raise Exception("Related entity has no ID and cascade=False")
    
    # Check if already being saved (circular ref)
    entity_hash = id(entity)
    if entity_hash in self._entity_tracker:
        raise Exception("Circular reference detected")
    
    # Save entity
    self._entity_tracker.add(entity_hash)
    # ... perform save ...
    return entity_id
```

---

## Next Steps

1. **Start with Phase 3a**
2. **Implement each step sequentially**
3. **Write tests as you go**
4. **Run tests frequently**
5. **Move to next phase only when current is stable**

Good luck! 🚀
