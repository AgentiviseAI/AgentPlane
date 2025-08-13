from typing import Optional, Dict, Any
from uuid import UUID
from app.schemas import ExecuteRequest, ExecuteResponse
from app.repositories import ConversationRepository
from app.core.logging import logger
from app.core.metrics import metrics, time_operation, TimingContext
from app.workflow.base import WorkflowProcessor
from app.workflow import NODE_REGISTRY
from app.services.cache_service import CacheService
from app.middleware.controltower_client import ControlTowerClient
from app.services.llm_service import LLMService


class WorkflowService:
    """Service for managing workflows and processing prompts"""
    
    def __init__(self, conversation_repository: ConversationRepository, 
                 cache_service: CacheService, controltower_client: ControlTowerClient,
                 llm_service: LLMService):
        self.conversation_repository = conversation_repository
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
            workflow = await self.get_workflow(agent.get("workflow_id"))
            if not workflow:
                logger.error(f"Workflow not found: {agent.get('workflow_id')}")
                metrics.increment_counter("workflow_service.execute", 1, {"status": "workflow_not_found"})
                raise ValueError(f"Workflow not found: {agent.get('workflow_id')}")
            
            # 3. Generate runid if not provided
            runid = request.runid if request.runid else str(uuid.uuid4())
            
            # 4. Create initial state
            initial_state = {
                "prompt": request.prompt,
                "runid": runid,
                "userid": str(user_id),  # Use user_id from auth context
                "agentid": request.agentid,
                "final_llm_response": "",
                "created_at": str(uuid.uuid4())  # Placeholder timestamp
            }
            
            logger.debug(f"Initial state created for run: {runid}")
            
            # 5. Execute workflow
            workflow_definition = {
                "nodes": workflow.get("nodes", []),
                "edges": workflow.get("edges", [])
            }
            
            logger.info(f"Executing workflow: {workflow.get('name')}")
            try:
                final_state = await self.execute_workflow(
                    workflow_definition, 
                    initial_state
                )
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                raise
            
            # 6. Store conversation
            from app.models.conversation import Conversation
            conversation = Conversation(
                userid=str(user_id),  # Use user_id from auth context
                chatid=runid,
                prompt=request.prompt,
                workflow_state=final_state,
                agent_id=agent.get("id"),
                workflow_id=workflow.get("id")
            )
            
            # Save to database using repository
            saved_conversation = await self.conversation_repository.create(conversation)
            logger.info(f"Conversation saved: {saved_conversation.id}")
            
            # 7. Update cache
            cache_key = f"conversation:{user_id}:{runid}"  # Use user_id from auth context
            await self.cache_service.set(cache_key, final_state, ttl=3600)  # 1 hour TTL
            
            # 8. Return response
            response = ExecuteResponse(
                agentid=request.agentid,
                response=final_state.get("final_llm_response", ""),
                runid=runid,
                userid=str(user_id)  # Use user_id from auth context
            )
            
            logger.info(f"Agent workflow executed successfully for run: {runid}")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "success"})
            
            return response
