from typing import Optional, Dict, Any
from uuid import UUID
import json
from app.schemas import ExecuteRequest, ExecuteResponse
from app.core.logging import logger
from app.core.metrics import metrics, time_operation, TimingContext
from app.workflow.base import WorkflowProcessor
from app.workflow import NODE_REGISTRY
from app.services.cache_service import CacheService
from app.services.conversation_service import ConversationService
from app.middleware.controltower_client import ControlTowerClient
from app.services.llm_service import LLMService


def serialize_workflow_state(obj):
    """Convert UUID objects to strings for JSON serialization"""
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_workflow_state(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_workflow_state(item) for item in obj]
    else:
        return obj


class WorkflowService:
    """Service for managing workflows and processing prompts"""
    
    def __init__(self, conversation_service: ConversationService, 
                 cache_service: CacheService, controltower_client: ControlTowerClient,
                 llm_service: LLMService):
        self.conversation_service = conversation_service
        self.cache_service = cache_service
        self.controltower_client = controltower_client
        self.llm_service = llm_service
        
        # Prepare services for dependency injection
        self.services = {
            "llm_service": self.llm_service
        }
    
    @time_operation("workflow_service.get_workflow")
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID from ControlTower"""
        try:
            logger.info(f"Fetching workflow by ID: {workflow_id}")
            
            workflow = await self.controltower_client.get_workflow(workflow_id)
            
            if workflow:
                logger.info(f"Found workflow: {workflow}")
                metrics.increment_counter("workflow_service.get_workflow", 1, {"status": "found"})
            else:
                logger.warning(f"Workflow not found: {workflow_id}")
                metrics.increment_counter("workflow_service.get_workflow", 1, {"status": "not_found"})
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error getting workflow by id {workflow_id}: {e}")
            metrics.increment_counter("workflow_service.get_workflow", 1, {"status": "error"})
            raise
    
    @time_operation("workflow_service.get_agent")
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID from ControlTower"""
        try:
            logger.info(f"Fetching agent by ID: {agent_id}")
            
            agent = await self.controltower_client.get_agent(agent_id)
            
            if agent:
                logger.info(f"Found agent: {agent}")
                metrics.increment_counter("workflow_service.get_agent", 1, {"status": "found"})
            else:
                logger.warning(f"Agent not found: {agent_id}")
                metrics.increment_counter("workflow_service.get_agent", 1, {"status": "not_found"})
            
            return agent
            
        except Exception as e:
            logger.error(f"Error getting agent by id {agent_id}: {e}")
            metrics.increment_counter("workflow_service.get_agent", 1, {"status": "error"})
            raise
    
    @time_operation("workflow_service.execute")
    async def execute_workflow(self, workflow_definition: Dict[str, Any], initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using WorkflowProcessor"""
        try:
            logger.info("Executing workflow")
            
            # Validate workflow definition
            if not workflow_definition.get("nodes") or not workflow_definition.get("edges"):
                raise ValueError("Workflow definition must contain 'nodes' and 'edges'")
            
            processor = WorkflowProcessor(workflow_definition, NODE_REGISTRY, services=self.services)
            result = await processor.execute(initial_state)
            
            logger.info("Workflow executed successfully")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "success"})
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "error"})
            raise
    
    async def execute(self, request: ExecuteRequest, user_id: UUID, organization_id: UUID, agent_id: UUID) -> ExecuteResponse:
        """Execute agent workflow with user prompt"""
        import uuid
        
        with TimingContext(metrics, "workflow_service.execute"):
            logger.info(f"Executing agent workflow for agent: {agent_id} (auth agent: {agent_id}), user: {user_id}, org: {organization_id}")
            
            # 1. Fetch agent details (ControlTowerClient will automatically use auth context)
            agent = await self.get_agent(str(agent_id))
            if not agent:
                logger.error(f"Agent not found: {agent_id}")
                metrics.increment_counter("workflow_service.execute", 1, {"status": "agent_not_found"})
                raise ValueError(f"Agent not found: {agent_id}")
            
            # 2. Fetch workflow definition (ControlTowerClient will automatically use auth context)
            workflow = await self.get_workflow(agent.workflow_id)
            if not workflow:
                logger.error(f"Workflow not found: {agent.workflow_id}")
                metrics.increment_counter("workflow_service.execute", 1, {"status": "workflow_not_found"})
                raise ValueError(f"Workflow not found: {agent.workflow_id}")
            
            # 3. Generate runid if not provided
            runid = request.runid if request.runid else str(uuid.uuid4())
            
            # 4. Create initial state
            initial_state = {
                "prompt": request.prompt,
                "runid": runid,
                "userid": str(user_id),  # Use user_id from auth context
                "agentid": str(agent_id),  # Convert UUID to string
                "final_llm_response": "",
                "created_at": str(uuid.uuid4())  # Placeholder timestamp
            }
            
            logger.debug(f"Initial state created for run: {runid}")
            
            # 5. Execute workflow
            workflow_definition = {
                "nodes": workflow.nodes or [],
                "edges": workflow.edges or []
            }
            
            logger.info(f"Executing workflow: {workflow.name}")
            try:
                final_state = await self.execute_workflow(
                    workflow_definition, 
                    initial_state
                )
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                raise
            
            # 6. Store conversation
            # Serialize workflow state to handle UUID objects
            serialized_workflow_state = serialize_workflow_state(final_state)
            
            conversation_data = {
                "userid": str(user_id),  # Use user_id from auth context
                "chatid": runid,
                "prompt": request.prompt,
                "workflow_state": serialized_workflow_state,
                "agent_id": agent.id,
                "workflow_id": workflow.id
            }
            
            # Save to database using conversation service
            conversation_id = await self.conversation_service.save_conversation(conversation_data)
            logger.info(f"Conversation saved: {conversation_id}")
            
            # 7. Update cache
            cache_key = f"conversation:{user_id}:{runid}"  # Use user_id from auth context
            await self.cache_service.set(cache_key, final_state, ttl=3600)  # 1 hour TTL
            
            # 8. Return response
            response = ExecuteResponse(
                agentid=agent_id,
                response=final_state.get("final_llm_response", ""),
                runid=runid,
                userid=str(user_id)  # Use user_id from auth context
            )
            
            logger.info(f"Agent workflow executed successfully for run: {runid}")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "success"})
            
            return response
