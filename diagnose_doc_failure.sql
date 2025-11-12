-- 诊断文档索引失败的SQL查询
-- 使用方式: psql -h <host> -U <user> -d <database> -f diagnose_doc_failure.sql

-- 查询变电站相关文档的信息
\echo '========================================';
\echo '查找变电站相关文档';
\echo '========================================';

SELECT 
    d.id AS document_id,
    d.name AS document_name,
    d.status AS document_status,
    d.collection_id,
    d.size,
    d.gmt_created,
    d.gmt_updated
FROM 
    document d
WHERE 
    d.name LIKE '%变电站%'
ORDER BY 
    d.gmt_created DESC
LIMIT 5;

\echo '';
\echo '========================================';
\echo '查询文档的索引状态';
\echo '========================================';

SELECT 
    di.document_id,
    d.name AS document_name,
    di.index_type,
    di.status AS index_status,
    di.version,
    di.error_message,
    di.gmt_created,
    di.gmt_updated
FROM 
    document_index di
JOIN 
    document d ON di.document_id = d.id
WHERE 
    d.name LIKE '%变电站%'
ORDER BY 
    di.document_id, di.index_type;

\echo '';
\echo '========================================';
\echo '查询失败的索引详情';
\echo '========================================';

SELECT 
    d.name AS document_name,
    di.index_type,
    di.status,
    di.error_message,
    di.gmt_updated AS failed_at
FROM 
    document_index di
JOIN 
    document d ON di.document_id = d.id
WHERE 
    d.name LIKE '%变电站%'
    AND di.status = 'FAILED'
ORDER BY 
    di.gmt_updated DESC;

\echo '';
\echo '========================================';
\echo '查询最近失败的所有文档索引';
\echo '========================================';

SELECT 
    d.name AS document_name,
    di.index_type,
    di.error_message,
    di.gmt_updated AS failed_at
FROM 
    document_index di
JOIN 
    document d ON di.document_id = d.id
WHERE 
    di.status = 'FAILED'
ORDER BY 
    di.gmt_updated DESC
LIMIT 10;

