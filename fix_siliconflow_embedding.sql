-- 修复SiliconFlow Embedding配置问题
-- 问题: 模型调用时custom_llm_provider传递了错误的值
-- 解决: 确保custom_llm_provider设置为'openai'(因为SiliconFlow兼容OpenAI API)

-- 1. 更新SiliconFlow provider的dialect设置(确保正确)
UPDATE llm_provider 
SET 
    embedding_dialect = 'openai',
    gmt_updated = NOW()
WHERE name = 'siliconflow';

-- 2. 更新SiliconFlow的embedding模型配置
UPDATE llm_provider_models 
SET 
    custom_llm_provider = 'openai',
    gmt_updated = NOW()
WHERE provider_name = 'siliconflow' 
  AND api = 'embedding';

-- 3. 查看更新后的配置
SELECT 
    provider_name, 
    api, 
    model, 
    custom_llm_provider 
FROM llm_provider_models 
WHERE provider_name = 'siliconflow' 
  AND api = 'embedding';

-- 4. 查看provider配置
SELECT 
    name, 
    embedding_dialect, 
    base_url 
FROM llm_provider 
WHERE name = 'siliconflow';

