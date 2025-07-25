# # Copyright (c) 2024 Microsoft Corporation.
# # Licensed under the MIT License

# """A module containing cluster_graph, apply_clustering and run_layout methods definition."""

# import logging

# import networkx as nx
# from graspologic.partition import hierarchical_leiden

# from graphrag.index.utils.stable_lcc import stable_largest_connected_component

# Communities = list[tuple[int, int, int, list[str]]]


# logger = logging.getLogger(__name__)


# def cluster_graph(
#     graph: nx.Graph,
#     max_cluster_size: int,
#     use_lcc: bool,
#     seed: int | None = None,
# ) -> Communities:
#     """Apply a hierarchical clustering algorithm to a graph."""
#     if len(graph.nodes) == 0:
#         logger.warning("Graph has no nodes")
#         return []

#     node_id_to_community_map, parent_mapping = _compute_leiden_communities(
#         graph=graph,
#         max_cluster_size=max_cluster_size,
#         use_lcc=use_lcc,
#         seed=seed,
#     )

#     levels = sorted(node_id_to_community_map.keys())

#     clusters: dict[int, dict[int, list[str]]] = {}
#     for level in levels:
#         result = {}
#         clusters[level] = result
#         for node_id, raw_community_id in node_id_to_community_map[level].items():
#             community_id = raw_community_id
#             if community_id not in result:
#                 result[community_id] = []
#             result[community_id].append(node_id)

#     results: Communities = []
#     for level in clusters:
#         for cluster_id, nodes in clusters[level].items():
#             results.append((level, cluster_id, parent_mapping[cluster_id], nodes))
#     return results


# # Taken from graph_intelligence & adapted
# def _compute_leiden_communities(
#     graph: nx.Graph | nx.DiGraph,
#     max_cluster_size: int,
#     use_lcc: bool,
#     seed: int | None = None,
# ) -> tuple[dict[int, dict[str, int]], dict[int, int]]:
#     """Return Leiden root communities and their hierarchy mapping."""
#     if use_lcc:
#         graph = stable_largest_connected_component(graph)

#     community_mapping = hierarchical_leiden(
#         graph, max_cluster_size=max_cluster_size, random_seed=seed
#     )
#     results: dict[int, dict[str, int]] = {}
#     hierarchy: dict[int, int] = {}
#     for partition in community_mapping:
#         results[partition.level] = results.get(partition.level, {})
#         results[partition.level][partition.node] = partition.cluster

#         hierarchy[partition.cluster] = (
#             partition.parent_cluster if partition.parent_cluster is not None else -1
#         )

#     return results, hierarchy






# =-------------------------------------------------------------------------------

import logging
import networkx as nx
from graspologic.partition import hierarchical_leiden
from graphrag.index.utils.stable_lcc import stable_largest_connected_component
from evoc import EVoC
from sklearn.manifold import SpectralEmbedding
from typing import Any
import numpy as np
import itertools
import community as community_louvain
from networkx.algorithms.community import (
    label_propagation_communities,
    girvan_newman,
)

Communities = list[tuple[int, int, int, list[str]]]
logger = logging.getLogger(__name__)

def cluster_graph(
    graph: nx.Graph,
    max_cluster_size: int,
    use_lcc: bool,
    method: str = "evoc",
    min_cluster_size: int = 2,
    seed: int | None = None,
) -> Communities:
    """Apply a clustering algorithm to a graph.

    method: 'leiden', 'evoc', 'louvain', 'label_prop', 'girvan_newman'
    evoc_min_size: minimum cluster size for EVōC.
    """
    if len(graph.nodes) == 0:
        logger.warning("Graph has no nodes")
        return []

    # 可选：只对最大连通子图做聚类
    if use_lcc:
        graph = stable_largest_connected_component(graph)

    if method == "evoc":
        node_map, parent_map = _compute_evoc_communities(graph, min_cluster_size=min_cluster_size, max_cluster_size=max_cluster_size, seed=seed)
    elif method == "louvain":
        node_map, parent_map = _compute_louvain_communities(graph)
    elif method == "label_prop":
        node_map, parent_map = _compute_label_prop_communities(graph)
    elif method == "girvan_newman":
        node_map, parent_map = _compute_girvan_newman_communities(graph)
    else:
        # 默认使用 Leiden
        node_map, parent_map = _compute_leiden_communities(
            graph, max_cluster_size, seed
        )

    # 将映射转换为 Communities 列表
    results: Communities = []
    for level, mapping in node_map.items():
        for cid, members in mapping.items():
            parent = parent_map.get(cid, -1)
            results.append((level, cid, parent, members))
    return results

# --------- 算法实现 ----------

def _compute_leiden_communities(graph, max_cluster_size, seed=None):
    community_mapping = hierarchical_leiden(
        graph, max_cluster_size=max_cluster_size, random_seed=seed
    )
    results = {}
    hierarchy = {}
    for partition in community_mapping:
        lvl = partition.level
        results.setdefault(lvl, {}).setdefault(partition.cluster, []).append(partition.node)
        hierarchy[partition.cluster] = (
            partition.parent_cluster if partition.parent_cluster is not None else -1
        )
    return results, hierarchy


# Evoc parameters
# def __init__(
#     self,
#     noise_level: float = 0.5,
#     base_min_cluster_size: int = 5,
#     base_n_clusters: int | None = None,
#     min_num_clusters: int = 4,
#     approx_n_clusters: int | None = None,
#     n_neighbors: int = 15,
#     min_samples: int = 5,
#     next_cluster_size_quantile: float = 0.8,
#     n_epochs: int = 50,
#     node_embedding_init: str | None = "label_prop",
#     symmetrize_graph: bool = True,
#     node_embedding_dim: int | None = None,
#     neighbor_scale: float = 1.0,
# ) -> None:


def _compute_evoc_communities(
    graph: nx.Graph,
    min_cluster_size: int,
    max_cluster_size: int,
    seed: int | None = None,
) -> tuple[dict[int, dict[int, list[Any]]], dict[int, int]]:
    """
    用 EVoC 对图做多层次递归聚类。
    - graph: 要聚类的图
    - min_cluster_size: EVoC 最小簇大小
    - max_cluster_size: 超过这个大小就递归再划分
    - seed: 随机种子
    返回 (mapping, parent)，其中
      mapping[level][cluster_id] = [node, ...]
      parent[cluster_id] = 上一级 cluster_id 或 -1
    """
    mapping: dict[int, dict[int, list[Any]]] = {}
    parent: dict[int, int] = {}
    next_cid = 0

    def recurse(subg: nx.Graph, level: int, parent_cid: int):
        nonlocal next_cid
        n = subg.number_of_nodes()
        if n == 0:
            return
        # 为这个子图分配一个新的 cluster_id
        cid = next_cid
        next_cid += 1

        mapping.setdefault(level, {})[cid] = list(subg.nodes())
        parent[cid] = parent_cid

        # 如果还需要进一步拆分
        if n > max_cluster_size:
            # 做 spectral embedding
            adj = nx.to_numpy_array(subg, weight="weight")
            n_comp = min(n - 1, 64)
            emb = SpectralEmbedding(
                n_components=n_comp,
                affinity="precomputed",
                random_state=seed,
            )
            X = emb.fit_transform(adj)

            # 运行 EVoC
            try:
                clusterer = EVoC(
                    base_min_cluster_size=min_cluster_size
                )
                labels = clusterer.fit_predict(X)
                if len(labels) == 0:
                    raise ValueError("no labels")
            except Exception:
                # EVoC 出错就跳过进一步拆分
                return

            # 按标签拆分，再递归
            clusters: dict[int, list[Any]] = {}
            for node, lbl in zip(subg.nodes(), labels):
                clusters.setdefault(int(lbl), []).append(node)

            for lbl, members in clusters.items():
                child_subg = subg.subgraph(members)
                recurse(child_subg, level + 1, cid)

    # 从根开始
    recurse(graph, level=0, parent_cid=-1)
    return mapping, parent


def _compute_louvain_communities(graph):
    if community_louvain is None:
        raise ImportError("Need python-louvain for 'louvain' method")
    part = community_louvain.best_partition(graph)
    mapping: dict[int, dict[int, list[Any]]] = {0: {}}  # single level
    for node, cid in part.items():
        mapping[0].setdefault(cid, []).append(node)
    parent: dict[int, int] = {cid: -1 for cid in mapping[0].keys()}
    return mapping, parent


def _compute_label_prop_communities(graph):
    communities = label_propagation_communities(graph)
    mapping: dict[int, dict[int, list[Any]]] = {0: {}}
    for cid, comm in enumerate(communities):
        mapping[0][cid] = list(comm)
    parent: dict[int, int] = {cid: -1 for cid in mapping[0].keys()}
    return mapping, parent


def _compute_girvan_newman_communities(graph):
    # 取 Girvan-Newman 第一次分裂结果
    comp_gen = girvan_newman(graph)
    first_level = tuple(sorted(c) for c in next(comp_gen))
    mapping: dict[int, dict[int, list[Any]]] = {0: {i: list(members) for i, members in enumerate(first_level)}}
    parent: dict[int, int] = {i: -1 for i in mapping[0].keys()}
    return mapping, parent
