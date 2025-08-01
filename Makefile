# Makefile for running GraphRAG indexing with different clustering methods
METHOD        ?= standard
CLUSTER_METHOD?= leiden
CONFIG        ?= settings.yaml
ROOT_DIR      ?= ragtest

.PHONY: run           run-standard    run-fast    run-louvain    run-evoc

run:
	cd $(ROOT_DIR) && \
	graphrag index \
	  --root . \
	  --config $(CONFIG) \
	  --method $(METHOD) \
	  --cluster-method $(CLUSTER_METHOD)

## 预设 target：Standard + 默认 cluster method (leiden)
run-standard:
	$(MAKE) run METHOD=standard

run-fast:
	$(MAKE) run METHOD=fast

run-leiden:
	$(MAKE) run CLUSTER_METHOD=leiden

run-louvain:
	$(MAKE) run CLUSTER_METHOD=louvain

run-evoc:
	$(MAKE) run CLUSTER_METHOD=evoc





# -------------------------------------------------------------------
# 默认参数（可通过命令行覆盖）
# -------------------------------------------------------------------
ROOT_DIR         ?= ragtest
DATA_DIR         ?= $(ROOT_DIR)/output
METHOD_Q         ?= global
QUERY            ?= "Give all doc ids related to AI"
COMMUNITY_LEVEL  ?= 2
RESPONSE_TYPE    ?= "Multiple Paragraphs"
STREAMING        ?= false

# -------------------------------------------------------------------
# 通用 query 命令
# -------------------------------------------------------------------
.PHONY: query query-local query-global query-drift

query:
	cd $(ROOT_DIR) && \
	graphrag query \
	  --method $(METHOD_Q) \
	  --query $(QUERY) \
	  --data $(DATA_DIR) \
	  --community-level $(COMMUNITY_LEVEL) \
	  --response-type $(RESPONSE_TYPE) \
	  --streaming=$(STREAMING)

# -------------------------------------------------------------------
# 预设 target：本地搜索（LOCAL）
# -------------------------------------------------------------------
query-local:
	$(MAKE) query METHOD_Q=local QUERY="$(QUERY)"

# -------------------------------------------------------------------
# 预设 target：全局搜索（GLOBAL）
# -------------------------------------------------------------------
query-global:
	$(MAKE) query METHOD_Q=global QUERY="$(QUERY)"

# -------------------------------------------------------------------
# 预设 target：漂移搜索（DRIFT）
# -------------------------------------------------------------------
query-drift:
	$(MAKE) query METHOD_Q=drift QUERY="$(QUERY)" 