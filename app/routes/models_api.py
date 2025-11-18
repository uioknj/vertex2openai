@router.get("/v1/models")
async def list_models(fastapi_request: Request, api_key: str = Depends(get_api_key)):
    await refresh_models_config_cache()
    
    PAY_PREFIX = "[PAY]"
    EXPRESS_PREFIX = ""  # 改为空字符串，取消 [EXPRESS] 前缀
    
    credential_manager_instance: CredentialManager = fastapi_request.app.state.credential_manager
    express_key_manager_instance = fastapi_request.app.state.express_key_manager

    has_sa_creds = credential_manager_instance.get_total_credentials() > 0
    has_express_key = express_key_manager_instance.get_total_keys() > 0

    raw_vertex_models = await get_vertex_models()
    raw_express_models = await get_vertex_express_models()
    
    final_model_list: List[Dict[str, Any]] = []
    processed_ids: Set[str] = set()
    current_time = int(time.time())

    def add_model_and_variants(base_id: str, prefix: str):
        """Adds a model to the list if not already present."""
        
        # 直接使用基础模型，不生成任何后缀变体
        model_id_with_suffix = base_id  # 直接使用基础ID，不加任何后缀
            
        # Experimental models have no prefix
        final_id = f"{prefix}{model_id_with_suffix}" if "-exp-" not in base_id else model_id_with_suffix

        if final_id not in processed_ids:
            final_model_list.append({
                "id": final_id,
                "object": "model",
                "created": current_time,
                "owned_by": "google",
                "permission": [],
                "root": base_id,
                "parent": None
            })
            processed_ids.add(final_id)

    # Process Express Key models first
    if has_express_key:
        for model_id in raw_express_models:
            add_model_and_variants(model_id, EXPRESS_PREFIX)

    # Process Service Account (PAY) models, they have lower priority
    if has_sa_creds:
        for model_id in raw_vertex_models:
            add_model_and_variants(model_id, PAY_PREFIX)

    return {"object": "list", "data": sorted(final_model_list, key=lambda x: x['id'])}
