from abc import ABC, abstractmethod
from typing import Dict, Any, List


class PipelineNode(ABC):
    """Abstract base class for all pipeline nodes"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        self.node_id = node_id
        self.config = config or {}
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state and return updated state"""
        pass


class PipelineProcessor:
    """Processes a pipeline definition by executing nodes in order"""
    
    def __init__(self, pipeline_definition: Dict[str, Any], node_registry: Dict[str, type]):
        self.definition = pipeline_definition
        self.node_registry = node_registry
        self.nodes = {}
        self._build_nodes()
    
    def _build_nodes(self):
        """Build node instances from pipeline definition"""
        for node_def in self.definition.get("nodes", []):
            node_type = node_def["type"]
            node_id = node_def["id"]
            config = node_def.get("config", {})
            
            if node_type not in self.node_registry:
                raise ValueError(f"Unknown node type: {node_type}")
            
            node_class = self.node_registry[node_type]
            # Pass the full node definition as config so nodes can access 'link' and other root-level fields
            full_config = {**config, **{k: v for k, v in node_def.items() if k not in ['type', 'id', 'config']}}
            self.nodes[node_id] = node_class(node_id, full_config)
    
    def _get_next_nodes(self, current_node_id: str) -> List[str]:
        """Get the next nodes to execute based on edges"""
        next_nodes = []
        for edge in self.definition.get("edges", []):
            # Handle both edge formats
            source = edge.get("source") or edge.get("source_component_id")
            target = edge.get("target") or edge.get("target_component_id")
            
            if source == current_node_id:
                next_nodes.append(target)
        return next_nodes
    
    async def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the pipeline starting from start_node"""
        # Auto-detect start and end nodes if not specified
        if "start_node" in self.definition:
            start_node = self.definition["start_node"]
        else:
            # Find node with type "start" or the first node that has no incoming edges
            start_candidates = [node["id"] for node in self.definition.get("nodes", []) if node.get("type") == "start"]
            if start_candidates:
                start_node = start_candidates[0]
            else:
                # Find first node with no incoming edges
                all_targets = set()
                for edge in self.definition.get("edges", []):
                    if "target" in edge:
                        all_targets.add(edge["target"])
                    elif "target_component_id" in edge:
                        all_targets.add(edge["target_component_id"])
                
                all_nodes = [node["id"] for node in self.definition.get("nodes", [])]
                start_candidates = [node_id for node_id in all_nodes if node_id not in all_targets]
                start_node = start_candidates[0] if start_candidates else all_nodes[0] if all_nodes else None
        
        if "end_node" in self.definition:
            end_node = self.definition["end_node"]
        else:
            # Find node with type "end"
            end_candidates = [node["id"] for node in self.definition.get("nodes", []) if node.get("type") == "end"]
            end_node = end_candidates[0] if end_candidates else None
        
        current_state = initial_state.copy()
        current_node_id = start_node
        
        while current_node_id and current_node_id != end_node:
            if current_node_id not in self.nodes:
                raise ValueError(f"Node not found: {current_node_id}")
            
            # Execute current node
            node = self.nodes[current_node_id]
            current_state = await node.process(current_state)
            
            # Get next node (assuming linear flow for now)
            next_nodes = self._get_next_nodes(current_node_id)
            current_node_id = next_nodes[0] if next_nodes else None
        
        # Execute end node if it exists
        if current_node_id == end_node and end_node in self.nodes:
            end_node_instance = self.nodes[end_node]
            current_state = await end_node_instance.process(current_state)
        
        return current_state
