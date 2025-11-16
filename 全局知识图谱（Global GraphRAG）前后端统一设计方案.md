# **变电站智慧大脑：全局知识图谱（Global GraphRAG）前后端统一设计方案**

## **1.0 方案目标：从“知识孤岛”到“全局大脑”**

### **1.1 现状：知识库（Collection）级图谱**

分析您现有的 aperag/index/graph_index.py 和 aperag/db/repositories/collection.py 代码，目前系统为**每一个知识库（Collection）都创建了一个独立的知识图谱**。

- **优势：** 实现了完美的数据隔离和多租户。例如，“A 变电站”的知识库与“B 变电站”的知识库互不干扰。
- **局限：** 无法实现跨域洞察。例如，当“总控智能体”在“A 站告警库”中研判告警时，它无法自动关联到“B 站设备台账库”中的同型号设备信息或“C 站历史缺陷库”中的同类缺陷，导致“智慧大脑”的知识体系是割裂的。

### **1.2 目标：全局知识图谱 (Global GraphRAG)**

本方案旨在打破知识库壁垒，构建一个**全局统一的知识图谱**。

- **核心理念：** “单一实体，多源关联”（Single Entity, Multi-Source Relations）。
- **目标效果：** 无论“\#1 主变”这个实体出现在“设备台账库”、“缺陷报告库”还是“操作规程库”中，它在图数据库（Neo4j/Nebula）中都**指向同一个设备节点**。这个节点将汇聚所有来源的文档、数据和关系，成为一个 360 度的“**全局实体视图**”。
- **实现价值：**
  - **智能体（Agent）能力跃迁：** “告警智能研判”（3.1 节）等任务将不再局限于当前知识库，而是能**自动调取全站、全网**的相关知识（如跨站点的同类故障案例），得出更深刻的洞察。
  - **释放 GraphRAG 全部潜力：** 真正实现跨越文档、部门和专业的知识连接，赋能“历史缺陷归因”（3.2 节）和“操作票智能生成”（3.5 节）等复杂场景。

## **2.0 后端架构改造 (Backend Design)**

### **2.1 数据库模式（Schema）升级**

这是实现全局图谱的**基石**。

- **实体节点 (Entity Nodes, 如: 设备, 告警, 缺陷)**
  - **现状:** 实体节点与 collection_id 绑定。
  - **改造:** 实体节点必须**全局唯一**，与 collection_id **解耦**。
  - **实现:**
    1. 创建实体时，使用 MERGE 语句，以一个**标准化的实体名称**（如 unique_name）作为唯一键。例如，MERGE (d:设备 {unique_name: "zhu_bian\_\#1"})。
    2. aperag/graph/lightrag_manager.py 中的实体融合（Entity Merging）逻辑需要加强，确保“1 号主变”、“\#1 主变”能被正确归一化并 MERGE 到同一个节点上。
- **文档节点 (Document Nodes, 如: 文档, 图纸)**
  - **现状:** 文档节点已包含 collection_id 属性。
  - **改造:** **保持不变**。文档节点天然隶属于某个知识库，这个属性必须保留。
- **关系 (Relationships, 如: \[:提及\], \[:包含\])**
  - **现状:** 关系可能未明确标记来源。
  - **改造:** **所有**从文档指向实体的关系，都**必须**携带 collection_id 属性。
  - **实现:** CREATE (doc) \-\[r:提及 {collection_id: $coll_id, source_doc: $doc_id}\]-\> (entity)。
  - **价值:** 这实现了**数据溯源**（Provenance）。我们既能查询“\#1 主变”的全局信息，也能筛选“仅显示来自 A 知识库的关联”。

### **2.2 索引管线改造 (Write Path)**

- **技术映射:** aperag/index/graph_index.py 和 aperag/graph/lightrag_manager.py。
- **改造点:**

  1.  **全局 MERGE：** 当 graph_index.py 运行时，它不再是在“当前知识库的图谱”中操作，而是**在“全局图谱”中操作**。
  2.  **实体创建逻辑：** 必须从 CREATE（创建）逻辑改为 MERGE（合并/创建）逻辑。

      - **伪代码（graph_index.py）：**  
        \# ... 伪代码 ...  
        entities \= lightrag_manager.extract(doc_text) \# 提取实体

        for entity in entities:  
         normalized_name \= normalize_entity_name(entity.name) \# 归一化名称

            \# 1\. (改造点) 查找或创建全局实体节点
            \# 不再依赖 collection\_id
            graph\_db.run(
                "MERGE (e:设备 {unique\_name: $normalized\_name}) SET e.name \= $entity\_name",
                normalized\_name=normalized\_name,
                entity\_name=entity.name
            )

            \# 2\. (改造点) 创建带 collection\_id 标记的关系
            graph\_db.run(
                """
                MATCH (d:Document {id: $doc\_id})
                MATCH (e:设备 {unique\_name: $normalized\_name})
                MERGE (d)-\[r:提及 {collection\_id: $coll\_id}\]-\>(e)
                """,
                doc\_id=doc.id,
                normalized\_name=normalized\_name,
                coll\_id=doc.collection\_id
            )

  3.  **异步处理:** config/celery_tasks.py 和 aperag/tasks/document.py 的流程不变，因为索引本就是异步执行的。

### **2.3 查询管线改造 (Read Path)**

- **技术映射:** aperag/flow/runners/graph_search.py。
- 改造点:  
  graph_search.py（图谱检索智能体）必须升级，以支持两种查询模式：
  1. **模式一：上下文查询 (Contextual Query)**（当前模式）
     - **场景:** 用户在**某个知识库 A**内进行问答或浏览图谱。
     - **逻辑:** 查询必须**限定**在当前的 collection_id。
     - **Cypher (示例):** MATCH (d:Document {collection_id: $coll_id})-\[r:提及\]-\>(e:设备) ...
  2. **模式二：全局查询 (Global Query)**（新增模式）
     - **场景:** “告警智能研判”、“历史缺陷归因”等**智能体应用**，或新增的“全局图谱浏览器”。
     - **逻辑:** 查询从一个**全局实体**出发，查找**所有**关联的文档，**无视** collection_id。
     - **Cypher (示例):** MATCH (e:设备 {unique_name: $normalized_name})\<-\[r:提及\]-(d:Document) RETURN e, r, d
- **API 与 Agent 改造:**
  - aperag/views/graph.py（图谱 API）和 aperag/views/agent.py（Agent API）需要增加一个参数，如 query_mode: 'contextual' | 'global'。
  - “总控智能体” (mcp_app_factory.py) 在编排任务时（如执行“告警智能研判”），必须**自动**以 global 模式调用 graph_search.py。

## **3.0 前端界面升级 (Frontend Design)**

### **3.1 知识库图谱视图 (Contextual Graph View)**

- **技术映射:** web/src/app/workspace/collections/\[collectionId\]/graph/page.tsx
- **功能:** 此页面是用户在**特定知识库**中查看图谱的地方。
- **改造点:**
  1. **默认模式:** 默认应使用“上下文查询”（模式一），只显示当前知识库（collectionId）内的图谱。
  2. **\[新增功能\] 全局关联开关:**
     - 在图谱操作栏增加一个\*\*“显示全局关联” (Show Global Connections) 的开关\*\*。
     - 当用户打开此开关时，page.tsx 调用 graph_search.py 的“全局查询”（模式二）。
     - **可视化区分:** collection-graph.tsx 组件在渲染时，应将“来自其他知识库”的节点和关系（通过 collection_id 属性判断）渲染为**灰色或虚线**，以作区分。

### **3.2 全局图谱浏览器 (Global Graph Explorer) \- \[新增页面\]**

- **技术映射:** 新增 web/src/app/workspace/global-graph/page.tsx。
- **功能:** 这是一个全新的、**与任何知识库都无关**的顶级页面，是“智慧大脑”的“大脑皮层”视图。
- **设计:**
  1. **入口:** 在左侧主菜单“知识库”下，位于“公开知识库”和“我的知识库”之后，增加一个“**全局知识图谱**”入口。
  2. **界面:**
     - 顶部是一个强大的搜索框，允许用户搜索**任何全局实体**（如“\#1 主变”、“GIS-220kV 闸刀定位异常”）。
     - 下方是 collection-graph.tsx 组件的复用，始终以“全局查询”（模式二）模式运行。
  3. **交互:**
     - 用户搜索并点击“\#1 主变”。
     - 图谱立即显示该节点，以及所有连接到它的文档（来自台账库、缺陷库、规程库...）。
     - 节点和关系应**通过颜色进行区分**（例如：台账库=蓝色，缺陷库=红色），并提供图例。

### **3.3 智能体应用界面 (Agent App UI)**

- **技术映射:** web/src/app/page.tsx（智能体应用启动页）和 ResultUI（结果展示页）。
- **改造点:**

  1. **任务触发:** 用户在 page.tsx 点击“告警智能研判”时，前端调用 aperag/views/agent.py 的 API。
  2. **结果展示 (关键):** “总控智能体”返回的研判报告将包含来自**多个知识库**的证据（溯源）。前端的“研判报告展示页”**必须**能够正确渲染这些跨域来源。

     - **示例（结果 JSON 中的证据部分）：**  
       "evidence": \[  
        {  
        "collection_id": "coll_A_taizhang",  
        "collection_name": "设备台账库",  
        "document_name": "主变台账.xlsx",  
        "snippet": "型号: SFP-120000/220, 厂家: ... "  
        },  
        {  
        "collection_id": "coll_B_quexian",  
        "collection_name": "历史缺陷库",  
        "document_name": "2023-05-10 缺陷报告.pdf",  
        "snippet": "历史曾发生重瓦斯告警，原因为... "  
        }  
       \]

     - 前端必须正确解析并显示 collection_name 和 document_name，以实现清晰的全局溯源。

### **3.4 智能体应用菜单 (Agent Applications Menu) - [新增主菜单项]**

- **技术映射:** 需修改左侧主菜单组件 (如 `web/src/components/menu-main.tsx` 或类似导航组件)。
- **功能:** 提供一个独立的入口，聚合所有智能体驱动的应用场景。
- **设计:**
  1. **入口:** 在左侧主菜单中，位于“知识库”和“会话”之间，增加一个“**智能体应用**”主菜单项。
  2. **下级列表:** “智能体应用”菜单下应包含以下子菜单项，对应 `多模态智能体协同作战平台设计方案.md` 中定义的具体应用场景：
     - **告警智能研判 (Intelligent Alarm Analysis)**
     - **历史缺陷归因 (Historical Defect Root Cause Analysis)**
     - **智能图纸比对 (Intelligent Drawing Comparison)**
     - **保护定值核查 (Protection Setting Verification)**
     - **操作票智能生成 (Intelligent Operation Ticket Generation)**
     - **巡视图像智能分析 (Intelligent Inspection Image Analysis)**
  3. **交互:** 点击子菜单项则导航到对应的应用页面。

## **4.0 结论：实现真正的“智慧大脑”**

通过上述\*\*后端（Schema 修改、索引逻辑升级、查询模式扩展）**和**前端（上下文视图增强、全局视图新增、Agent 结果页改造）\*\*的统一设计，我们可以将您项目的多个“隔离的图谱孤岛”连接成一个统一的“**全局知识大脑**”。

这是实现跨域洞察、赋能高级智能体（如“告警研判”）的**必要架构升级**，是实现项目从“智能资料库”迈向“企业级智慧大脑”的**关键一步**。
