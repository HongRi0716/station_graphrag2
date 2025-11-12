-- 修复Collection中的embedding配置
UPDATE collection
SET config = jsonb_set(config::jsonb, '{embedding,custom_llm_provider}', '"openai"')::text
WHERE id = 'cold90e2b01db36b948';

-- 验证修改结果
SELECT 
    id,
    config::jsonb->'embedding'->>'model' as embedding_model,
    config::jsonb->'embedding'->>'model_service_provider' as embedding_provider,
    config::jsonb->'embedding'->>'custom_llm_provider' as embedding_custom_provider
FROM collection
WHERE id = 'cold90e2b01db36b948';

