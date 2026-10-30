"""GNN Detector wrapper, training pipeline, and inference scoring for Component C."""

import json
from pathlib import Path
from typing import Dict, List, Literal, Optional
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from agentguard.graph.gnn_models import TrajectoryGAT, TrajectoryGraphSAGE
from agentguard.graph.trajectory_graph import TrajectoryGraph


class GNNDetector:
    """Component C GNN Detector wrapper supporting GraphSAGE and GAT architectures."""

    def __init__(
        self,
        model_type: Literal["graphsage", "gat"] = "graphsage",
        include_untrusted_flag: bool = True,
        hidden_channels: int = 32,
        device: str = "cpu",
    ):
        self.model_type = model_type
        self.include_untrusted_flag = include_untrusted_flag
        self.device = torch.device(device)

        in_channels = 8  # 4 onehot + priv + token_len + step_idx + untrusted_flag
        if model_type == "graphsage":
            self.model = TrajectoryGraphSAGE(in_channels=in_channels, hidden_channels=hidden_channels)
        else:
            self.model = TrajectoryGAT(in_channels=in_channels, hidden_channels=hidden_channels)

        self.model.to(self.device)
        self.is_trained = False

    def train(
        self,
        train_graphs: List[TrajectoryGraph],
        val_graphs: Optional[List[TrajectoryGraph]] = None,
        epochs: int = 25,
        lr: float = 0.005,
    ):
        """Train the GNN model using PyTorch Geometric DataLoader."""
        train_data_list = [g.to_pyg_data(include_untrusted_flag=self.include_untrusted_flag) for g in train_graphs]
        train_loader = DataLoader(train_data_list, batch_size=32, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-4)
        criterion = torch.nn.CrossEntropyLoss()

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0.0
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                logits = self.model(batch.x, batch.edge_index, batch.batch)
                loss = criterion(logits, batch.y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        self.is_trained = True

    def score(self, graph: TrajectoryGraph) -> float:
        """Score a single trajectory graph and return probability of malicious hijack [0.0, 1.0]."""
        self.model.eval()
        data = graph.to_pyg_data(include_untrusted_flag=self.include_untrusted_flag)
        data = data.to(self.device)

        with torch.no_grad():
            batch = torch.zeros(data.x.size(0), dtype=torch.long, device=self.device)
            logits = self.model(data.x, data.edge_index, batch)
            probs = F.softmax(logits, dim=-1)
            # Class 1 probability
            p_attack = probs[0, 1].item()
            return float(p_attack)

    def save(self, model_dir: Path):
        """Save GNN weights and configuration."""
        model_dir.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), model_dir / f"{self.model_type}_weights.pt")
        with open(model_dir / f"{self.model_type}_config.json", "w", encoding="utf-8") as f:
            json.dump({
                "model_type": self.model_type,
                "include_untrusted_flag": self.include_untrusted_flag,
            }, f, indent=2)

    def load(self, model_dir: Path):
        """Load GNN weights and configuration."""
        weights_path = model_dir / f"{self.model_type}_weights.pt"
        if weights_path.exists():
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
            self.is_trained = True
