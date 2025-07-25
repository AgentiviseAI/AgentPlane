from typing import Optional, Dict, Any
from app.models import Workflow
from app.schemas import ProcessPromptRequest, ProcessPromptResponse
from app.repositories import WorkflowRepository, AgentRepository, ConversationRepository
from app.core.logging import logger
from app.core.metrics import metrics, time_operation, TimingContext
from app.workflow.base import WorkflowProcessor
from app.workflow import NODE_REGISTRY
from app.services.cache_service import CacheService


class WorkflowService:
    """Service for managing workflows and processing prompts"""
    
    def __init__(self, workflow_repository: WorkflowRepository, agent_repository: AgentRepository, 
                 conversation_repository: ConversationRepository, cache_service: CacheService):
        self.workflow_repository = workflow_repository
        self.agent_repository = agent_repository
        self.conversation_repository = conversation_repository
        self.cache_service = cache_service
    
    @time_operation("workflow_service.get_by_id")
    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID (read-only operation)"""
        try:
            logger.info(f"Fetching workflow by ID: {workflow_id}")
            
            workflow = await self.workflow_repository.get_by_id(workflow_id)
            
            if workflow:
                logger.info(f"Found workflow: {workflow}")
                metrics.increment_counter("workflow_service.get_by_id", 1, {"status": "found"})
            else:
                logger.warning(f"Workflow not found: {workflow_id}")
                metrics.increment_counter("workflow_service.get_by_id", 1, {"status": "not_found"})
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error getting workflow by id {workflow_id}: {e}")
            metrics.increment_counter("workflow_service.get_by_id", 1, {"status": "error"})
            raise
    
    @time_operation("workflow_service.execute")
    async def execute_workflow(self, workflow_definition: Dict[str, Any], initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using WorkflowProcessor"""
        try:
            logger.info("Executing workflow")
            
            # Validate workflow definition
            if not workflow_definition.get("nodes") or not workflow_definition.get("edges"):
                raise ValueError("Workflow definition must contain 'nodes' and 'edges'")
            
            processor = WorkflowProcessor(workflow_definition, NODE_REGISTRY)
            result = await processor.execute(initial_state)
            
            logger.info("Workflow executed successfully")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "success"})
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            metrics.increment_counter("workflow_service.execute", 1, {"status": "error"})
            raise
    
    async def process_prompt(self, request: ProcessPromptRequest) -> ProcessPromptResponse:
        """Process a user prompt through the agent workflow"""
        import uuid
        
        with TimingContext(metrics, "workflow_service.process_prompt"):
            logger.info(f"Processing prompt for agent: {request.agentid}")
            
            # 1. Fetch agent details
            agent = await self.agent_repository.get_by_id(request.agentid)
            if not agent:
                logger.error(f"Agent not found: {request.agentid}")
                metrics.increment_counter("workflow_service.process_prompt", 1, {"status": "agent_not_found"})
                raise ValueError(f"Agent not found: {request.agentid}")
            
            # 2. Fetch workflow definition
            workflow = await self.workflow_repository.get_by_id(str(agent.workflow_id))
            if not workflow:
                logger.error(f"Workflow not found: {agent.workflow_id}")
                metrics.increment_counter("workflow_service.process_prompt", 1, {"status": "workflow_not_found"})
                raise ValueError(f"Workflow not found: {agent.workflow_id}")
            
            # 3. Generate chatid if not provided
            chatid = request.chatid if request.chatid else str(uuid.uuid4())
            
            # 4. Create initial state
            initial_state = {
                "prompt": request.prompt,
                "chatid": chatid,
                "userid": request.userid,
                "agentid": request.agentid,
                "final_llm_response": "",
                "created_at": str(uuid.uuid4())  # Placeholder timestamp
            }
            
            logger.debug(f"Initial state created for chat: {chatid}")
            
            # 5. Execute workflow
            workflow_definition = {
                "nodes": workflow.nodes,
                "edges": workflow.edges
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
            from app.models.conversation import Conversation
            conversation = Conversation(
                userid=request.userid,
                chatid=chatid,
                prompt=request.prompt,
                workflow_state=final_state,
                agent_id=str(agent.id),
                workflow_id=str(workflow.id)
            )
            
            # Save to database using repository
            saved_conversation = await self.conversation_repository.create(conversation)
            logger.info(f"Conversation saved: {saved_conversation.id}")
            
            # 7. Update cache
            cache_key = f"conversation:{request.userid}:{chatid}"
            await self.cache_service.set(cache_key, final_state, ttl=3600)  # 1 hour TTL
            
            # 8. Return response
            response = ProcessPromptResponse(
                agentid=request.agentid,
                response=final_state.get("final_llm_response", ""),
                chatid=chatid,
                userid=request.userid
            )
            
            logger.info(f"Prompt processed successfully for chat: {chatid}")
            metrics.increment_counter("workflow_service.process_prompt", 1, {"status": "success"})
            
            return response
