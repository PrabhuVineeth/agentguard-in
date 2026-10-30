"""Trajectory to Heterogeneous Influence Graph conversion for AgentGuard-IN."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
import numpy as np
import torch
from torch_geometric.data import Data
from agentguard.logging.schema import TrajectoryRun, TrajectoryStep


NODE_TYPE_MAP = {
    "user_request": 0,
    "model_step": 1,
    "tool_call": 2,
    "tool_result": 3,
}

PRIVILEGED_TOOLS = {"send_payment", "book_ticket"}


@dataclass
class GraphNode:
    node_id: int
    step_index: int
    node_type: str
    role: str
    tool_name: Optional[str] = None
    is_untrusted: bool = False
    is_privileged: bool = False
    token_len: int = 0
    text_snippet: str = ""


@dataclass
class GraphEdge:
    source_id: int
    target_id: int
    edge_type: str  # "control_flow" or "data_flow"


class TrajectoryGraph:
    """Graph representation of an agent's execution trajectory."""

    def __init__(self, run: TrajectoryRun):
        self.run_id = run.run_id
        self.task_id = run.task_id
        self.domain = run.domain
        self.is_attacked = run.is_attacked
        self.attack_family = run.attack_family
        self.attack_success = run.attack_success
        self.split = run.split
        self.language = run.language
        self.nodes: Dict[int, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._build_graph(run)

    def _build_graph(self, run: TrajectoryRun):
        """Construct nodes and causal influence edges from trajectory steps."""
        for step in run.steps:
            is_priv = False
            if step.step_type == "tool_call" and step.tool_name in PRIVILEGED_TOOLS:
                is_priv = True

            txt = step.content or ""
            if step.tool_args:
                txt += " " + str(step.tool_args)
            if step.tool_result:
                txt += " " + str(step.tool_result)

            node = GraphNode(
                node_id=step.step_index,
                step_index=step.step_index,
                node_type=step.step_type,
                role=step.role,
                tool_name=step.tool_name,
                is_untrusted=step.is_untrusted,
                is_privileged=is_priv,
                token_len=len(txt.split()),
                text_snippet=txt[:120],
            )
            self.nodes[step.step_index] = node

            # Build edges from parent step indices (influence / causal flow)
            for parent_idx in step.parent_step_indices:
                if parent_idx in self.nodes:
                    edge_type = "control_flow" if step.step_type in ("model_step", "tool_call") else "data_flow"
                    self.edges.append(
                        GraphEdge(source_id=parent_idx, target_id=step.step_index, edge_type=edge_type)
                    )

            # Sequential fallback edge if no parent explicit
            if not step.parent_step_indices and step.step_index > 0:
                self.edges.append(
                    GraphEdge(source_id=step.step_index - 1, target_id=step.step_index, edge_type="control_flow")
                )

    def to_networkx(self) -> nx.DiGraph:
        """Export as NetworkX DiGraph."""
        G = nx.DiGraph()
        for nid, node in self.nodes.items():
            G.add_node(
                nid,
                step_index=node.step_index,
                node_type=node.node_type,
                node_type_id=NODE_TYPE_MAP.get(node.node_type, 0),
                is_untrusted=node.is_untrusted,
                is_privileged=node.is_privileged,
                token_len=node.token_len,
            )
        for e in self.edges:
            G.add_edge(e.source_id, e.target_id, edge_type=e.edge_type)
        return G

    def to_pyg_data(self, include_untrusted_flag: bool = True) -> Data:
        """Convert to PyTorch Geometric Data object for GNN processing."""
        node_indices = sorted(self.nodes.keys())
        idx_map = {orig: i for i, orig in enumerate(node_indices)}

        x_features = []
        for orig in node_indices:
            node = self.nodes[orig]
            # One-hot node type (4 dims)
            type_onehot = [0.0] * 4
            t_id = NODE_TYPE_MAP.get(node.node_type, 0)
            type_onehot[t_id] = 1.0

            feats = type_onehot + [
                1.0 if node.is_privileged else 0.0,
                float(node.token_len) / 100.0,
                float(node.step_index) / 10.0,
            ]
            if include_untrusted_flag:
                feats.append(1.0 if node.is_untrusted else 0.0)
            else:
                feats.append(0.0)  # Ablated flag

            x_features.append(feats)

        x = torch.tensor(x_features, dtype=torch.float)

        edge_index_list = []
        edge_attr_list = []
        for e in self.edges:
            if e.source_id in idx_map and e.target_id in idx_map:
                edge_index_list.append([idx_map[e.source_id], idx_map[e.target_id]])
                edge_attr_list.append([1.0 if e.edge_type == "control_flow" else 0.0])

        if edge_index_list:
            edge_index = torch.tensor(edge_index_list, dtype=torch.long).t().contiguous()
            edge_attr = torch.tensor(edge_attr_list, dtype=torch.float)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            edge_attr = torch.empty((0, 1), dtype=torch.float)

        y_label = 1 if self.is_attacked else 0
        y = torch.tensor([y_label], dtype=torch.long)

        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
        data.task_id = self.task_id
        data.split = self.split
        data.domain = self.domain
        data.attack_family = self.attack_family or "none"
        data.language = self.language
        return data

    def extract_handcrafted_features(self, include_untrusted_flag: bool = True) -> Dict[str, float]:
        """Extract graph-theoretic topological features for baseline gradient boosting."""
        G = self.to_networkx()
        n_nodes = len(self.nodes)
        n_edges = len(self.edges)

        # Type counts
        counts = {nt: 0 for nt in NODE_TYPE_MAP}
        for n in self.nodes.values():
            counts[n.node_type] += 1

        n_untrusted = sum(1 for n in self.nodes.values() if n.is_untrusted)
        n_privileged = sum(1 for n in self.nodes.values() if n.is_privileged)

        # Path features: minimum distance from any untrusted node to any privileged tool call
        min_untrusted_to_privileged_dist = 99.0
        if n_untrusted > 0 and n_privileged > 0:
            untrusted_ids = [n.node_id for n in self.nodes.values() if n.is_untrusted]
            privileged_ids = [n.node_id for n in self.nodes.values() if n.is_privileged]

            for u in untrusted_ids:
                for p in privileged_ids:
                    if nx.has_path(G, u, p):
                        d = nx.shortest_path_length(G, u, p)
                        if d < min_untrusted_to_privileged_dist:
                            min_untrusted_to_privileged_dist = float(d)

        # Graph density & degree metrics
        density = nx.density(G) if n_nodes > 1 else 0.0
        in_degrees = [d for _, d in G.in_degree()]
        out_degrees = [d for _, d in G.out_degree()]
        max_in_deg = float(max(in_degrees)) if in_degrees else 0.0
        max_out_deg = float(max(out_degrees)) if out_degrees else 0.0

        features = {
            "n_nodes": float(n_nodes),
            "n_edges": float(n_edges),
            "density": float(density),
            "n_user": float(counts["user_request"]),
            "n_model": float(counts["model_step"]),
            "n_tool_call": float(counts["tool_call"]),
            "n_tool_result": float(counts["tool_result"]),
            "n_privileged": float(n_privileged),
            "max_in_deg": max_in_deg,
            "max_out_deg": max_out_deg,
        }

        if include_untrusted_flag:
            features.update({
                "n_untrusted": float(n_untrusted),
                "untrusted_ratio": float(n_untrusted / n_nodes) if n_nodes > 0 else 0.0,
                "untrusted_to_priv_path": min_untrusted_to_privileged_dist if min_untrusted_to_privileged_dist < 90 else -1.0,
                "has_untrusted_priv_flow": 1.0 if min_untrusted_to_privileged_dist < 90 else 0.0,
            })
        else:
            features.update({
                "n_untrusted": 0.0,
                "untrusted_ratio": 0.0,
                "untrusted_to_priv_path": -1.0,
                "has_untrusted_priv_flow": 0.0,
            })

        return features
