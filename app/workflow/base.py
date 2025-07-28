from abc import ABC, abstractmethod
from typing import Dict, Any, List, Set
import asyncio


class WorkflowNode(ABC):
    """Abstract base class for all workflow nodes"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        self.node_id = node_id
        self.config = config or {}
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the state and return updated state"""
        pass


class WorkflowProcessor:
    """Processes a workflow definition by executing nodes in order"""
    
    def __init__(self, workflow_definition: Dict[str, Any], node_registry: Dict[str, type]):
        self.definition = workflow_definition
        self.node_registry = node_registry
        self.nodes = {}
        self._build_nodes()
    
    def _build_nodes(self):
        """Build node instances from workflow definition"""
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
    
    def _get_previous_nodes(self, current_node_id: str) -> List[str]:
        """Get the previous nodes that point to the current node"""
        previous_nodes = []
        for edge in self.definition.get("edges", []):
            # Handle both edge formats
            source = edge.get("source") or edge.get("source_component_id")
            target = edge.get("target") or edge.get("target_component_id")
            
            if target == current_node_id:
                previous_nodes.append(source)
        return previous_nodes
    
    def _all_dependencies_completed(self, node_id: str, completed_nodes: Set[str]) -> bool:
        """Check if all dependencies (previous nodes) of a node have been completed"""
        previous_nodes = self._get_previous_nodes(node_id)
        return all(prev_node in completed_nodes for prev_node in previous_nodes)
    
    async def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with support for both sequential and parallel execution"""
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

        # Initialize workflow state
        current_state = initial_state.copy()
        completed_nodes: Set[str] = set()
        running_tasks: Dict[str, asyncio.Task] = {}
        
        # Start with the start node
        ready_nodes = [start_node] if start_node else []
        
        while ready_nodes or running_tasks:
            # Start all ready nodes in parallel
            for node_id in ready_nodes:
                if node_id not in self.nodes:
                    raise ValueError(f"Node not found: {node_id}")
                
                node = self.nodes[node_id]
                # Create a task for this node with a copy of current state
                task = asyncio.create_task(
                    self._execute_node_with_state(node, current_state.copy()),
                    name=f"node_{node_id}"
                )
                running_tasks[node_id] = task
            
            ready_nodes = []
            
            # Wait for at least one task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(), 
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    # Find which node this task belongs to
                    completed_node_id = None
                    for node_id, node_task in running_tasks.items():
                        if node_task == task:
                            completed_node_id = node_id
                            break
                    
                    if completed_node_id:
                        try:
                            # Get the result and merge it into current state
                            node_result = await task
                            current_state.update(node_result)
                            completed_nodes.add(completed_node_id)
                            
                            # Remove from running tasks
                            del running_tasks[completed_node_id]
                            
                            # Check if we've reached the end
                            if completed_node_id == end_node:
                                # Cancel any remaining tasks
                                for remaining_task in running_tasks.values():
                                    remaining_task.cancel()
                                break
                            
                            # Find next nodes that are ready to execute
                            next_nodes = self._get_next_nodes(completed_node_id)
                            for next_node in next_nodes:
                                if (next_node not in completed_nodes and 
                                    next_node not in running_tasks and 
                                    next_node not in ready_nodes and
                                    self._all_dependencies_completed(next_node, completed_nodes)):
                                    ready_nodes.append(next_node)
                        
                        except Exception as e:
                            # Cancel all running tasks if one fails
                            for remaining_task in running_tasks.values():
                                remaining_task.cancel()
                            raise RuntimeError(f"Node {completed_node_id} failed: {str(e)}") from e
        
        return current_state
    
    async def _execute_node_with_state(self, node: WorkflowNode, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node and return its result"""
        return await node.process(state)
    
    def get_execution_plan(self) -> Dict[str, Any]:
        """Get a visual representation of the workflow execution plan"""
        plan = {
            "nodes": {},
            "execution_levels": []
        }
        
        # Analyze dependency levels
        all_nodes = [node["id"] for node in self.definition.get("nodes", [])]
        processed = set()
        current_level = 0
        
        # Find start nodes (no dependencies)
        start_nodes = []
        for node_id in all_nodes:
            if not self._get_previous_nodes(node_id):
                start_nodes.append(node_id)
        
        current_level_nodes = start_nodes
        
        while current_level_nodes:
            plan["execution_levels"].append({
                "level": current_level,
                "nodes": current_level_nodes.copy(),
                "parallel": len(current_level_nodes) > 1
            })
            
            for node_id in current_level_nodes:
                plan["nodes"][node_id] = {
                    "level": current_level,
                    "dependencies": self._get_previous_nodes(node_id),
                    "next_nodes": self._get_next_nodes(node_id)
                }
                processed.add(node_id)
            
            # Find next level nodes
            next_level_nodes = []
            for node_id in current_level_nodes:
                for next_node in self._get_next_nodes(node_id):
                    if (next_node not in processed and 
                        next_node not in next_level_nodes and
                        self._all_dependencies_completed(next_node, processed)):
                        next_level_nodes.append(next_node)
            
            current_level_nodes = next_level_nodes
            current_level += 1
        
        return plan
