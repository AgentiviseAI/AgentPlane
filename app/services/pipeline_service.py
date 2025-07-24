from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Pipeline
from app.schemas import ProcessPromptRequest, ProcessPromptResponse
from app.core.logging import logger
from app.core.metrics import metrics, time_operation, TimingContext
from app.pipeline.base import PipelineProcessor
from app.pipeline import NODE_REGISTRY
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.services.cache_service import CacheService


class PipelineService:
    """Service for managing pipelines and processing prompts"""
    
    def __init__(self, session: AsyncSession, cache_service: CacheService):
        self.session = session
        self.cache_service = cache_service
        self.agent_service = AgentService(session)
        self.conversation_service = ConversationService(session)
    
    @time_operation("pipeline_service.get_by_id")
    async def get_by_id(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline by ID (read-only operation)"""
        try:
            logger.info(f"Fetching pipeline by ID: {pipeline_id}")
            
            result = await self.session.execute(
                select(Pipeline).where(Pipeline.id == pipeline_id)
            )
            pipeline = result.scalar_one_or_none()
            
            if pipeline:
                logger.info(f"Found pipeline: {pipeline}")
                metrics.increment_counter("pipeline_service.get_by_id", 1, {"status": "found"})
            else:
                logger.warning(f"Pipeline not found: {pipeline_id}")
                metrics.increment_counter("pipeline_service.get_by_id", 1, {"status": "not_found"})
            
            return pipeline
            
        except Exception as e:
            logger.error(f"Error getting pipeline by id {pipeline_id}: {e}")
            metrics.increment_counter("pipeline_service.get_by_id", 1, {"status": "error"})
            raise
    
    @time_operation("pipeline_service.execute")
    async def execute_pipeline(self, pipeline_definition: Dict[str, Any], initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline using PipelineProcessor"""
        try:
            logger.info("Executing pipeline")
            
            # Validate pipeline definition
            if not pipeline_definition.get("nodes") or not pipeline_definition.get("edges"):
                raise ValueError("Pipeline definition must contain 'nodes' and 'edges'")
            
            processor = PipelineProcessor(pipeline_definition, NODE_REGISTRY)
            result = await processor.execute(initial_state)
            
            logger.info("Pipeline executed successfully")
            metrics.increment_counter("pipeline_service.execute", 1, {"status": "success"})
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing pipeline: {e}")
            metrics.increment_counter("pipeline_service.execute", 1, {"status": "error"})
            raise
    
    async def process_prompt(self, request: ProcessPromptRequest) -> ProcessPromptResponse:
        """Process a user prompt through the agent pipeline"""
        import uuid
        
        with TimingContext(metrics, "pipeline_service.process_prompt"):
            logger.info(f"Processing prompt for agent: {request.agentid}")
            
            # 1. Fetch agent details
            agent = await self.agent_service.get_by_id(request.agentid)
            if not agent:
                logger.error(f"Agent not found: {request.agentid}")
                metrics.increment_counter("pipeline_service.process_prompt", 1, {"status": "agent_not_found"})
                raise ValueError(f"Agent not found: {request.agentid}")
            
            # 2. Fetch pipeline definition
            pipeline = await self.get_by_id(str(agent.pipeline_id))
            if not pipeline:
                logger.error(f"Pipeline not found: {agent.pipeline_id}")
                metrics.increment_counter("pipeline_service.process_prompt", 1, {"status": "pipeline_not_found"})
                raise ValueError(f"Pipeline not found: {agent.pipeline_id}")
            
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
            
            # 5. Execute pipeline
            pipeline_definition = {
                "nodes": pipeline.nodes,
                "edges": pipeline.edges
            }
            
            logger.info(f"Executing pipeline: {pipeline.name}")
            try:
                final_state = await self.execute_pipeline(
                    pipeline_definition, 
                    initial_state
                )
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                raise
            
            # 6. Store conversation
            conversation_data = {
                "userid": request.userid,
                "chatid": chatid,
                "prompt": request.prompt,
                "pipeline_state": final_state,
                "agent_id": str(agent.id),
                "pipeline_id": str(pipeline.id)
            }
            
            # Save to database
            conversation_id = await self.conversation_service.save_conversation(conversation_data)
            logger.info(f"Conversation saved: {conversation_id}")
            
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
            metrics.increment_counter("pipeline_service.process_prompt", 1, {"status": "success"})
            
            return response
