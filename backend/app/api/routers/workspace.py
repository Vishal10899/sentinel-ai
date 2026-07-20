"""Protected MVP workspace endpoints: execution, history, analytics, provider setup."""
from time import perf_counter
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import current_user
from app.api.schemas import PlaygroundRequest, ProviderConfigRequest
from app.auth.service import User
from app.cost import CostEstimator
from app.history.store import history_store
from app.models_registry import model_registry
from app.providers.manager import provider_manager
from app.routing import BalancedStrategy, CheapestStrategy, FastestStrategy, IntelligentRouter, ModelInfo

router=APIRouter(tags=["workspace"])
_strategies={"balanced":BalancedStrategy,"cheapest":CheapestStrategy,"fastest":FastestStrategy}

@router.post("/playground/execute")
async def execute(request: PlaygroundRequest, user: User=Depends(current_user)) -> dict[str, object]:
    available=[]
    for model in model_registry.list_models(enabled_only=True):
        if model.provider_id in provider_manager.provider_names():
            available.append(ModelInfo(model.provider_id,model.model_id,float(model.cost_per_1k_input_tokens+model.cost_per_1k_output_tokens),float(model.average_latency_ms),frozenset(request.task_category.__class__(cap) for cap in model.capabilities),model.priority))
    try: selected=IntelligentRouter(_strategies[request.strategy]()).select_model(request.task_category,available)
    except ValueError as error: raise HTTPException(status_code=422,detail=str(error)) from error
    metadata=model_registry.get_model(selected.provider,selected.model_name)
    estimate=CostEstimator().estimate_with_token_prices(metadata.provider_id,metadata.model_id,request.input_tokens,request.output_tokens,metadata.cost_per_1k_input_tokens,metadata.cost_per_1k_output_tokens)
    started=perf_counter()
    try: response=await provider_manager.get(selected.provider).generate(request.prompt,model=selected.model_name)
    except NotImplementedError: response="Provider generation is not configured. Add a provider API key in Settings to execute this prompt."
    item=history_store.add(user.user_id,prompt=request.prompt,provider_id=selected.provider,model_id=selected.model_name,response=response,estimated_cost_usd=str(estimate.estimated_cost),latency_ms=round((perf_counter()-started)*1000))
    return {**item.__dict__,"capabilities":sorted(metadata.capabilities),"reason":f"{request.strategy.title()} strategy selected this compatible model."}

@router.get("/history")
async def history(query: str="", user: User=Depends(current_user)) -> list[dict[str,object]]: return history_store.list(user.user_id,query)

@router.get("/analytics")
async def analytics(user: User=Depends(current_user)) -> dict[str,object]:
    items=history_store.list(user.user_id); total=sum(float(item["estimated_cost_usd"]) for item in items)
    providers={}
    for item in items: providers[item["provider_id"]]=providers.get(item["provider_id"],0)+1
    return {"total_requests":len(items),"estimated_cost_usd":total,"money_saved_usd":0,"provider_usage":[{"provider":k,"requests":v} for k,v in providers.items()],"recent_activity":items[:10]}

@router.put("/providers/{provider_id}/configuration")
async def configure_provider(provider_id: str, request: ProviderConfigRequest, _: User=Depends(current_user)) -> dict[str,str]:
    try: provider_manager.configure(provider_id,api_key=request.api_key,model=request.model,enabled=request.enabled)
    except KeyError as error: raise HTTPException(status_code=404,detail="Provider adapter not available") from error
    return await provider_manager.get(provider_id).health()

@router.post("/providers/{provider_id}/test")
async def test_provider(provider_id: str, _: User=Depends(current_user)) -> dict[str,str]:
    try: return await provider_manager.get(provider_id).health()
    except KeyError as error: raise HTTPException(status_code=404,detail="Provider adapter not available") from error
