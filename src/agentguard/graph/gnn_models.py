"""PyTorch Geometric Graph Neural Network architectures (GraphSAGE and GAT)."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv, SAGEConv, global_max_pool, global_mean_pool


class TrajectoryGraphSAGE(nn.Module):
    """Component C Main Model: GraphSAGE on agent trajectory influence graphs."""

    def __init__(self, in_channels: int = 8, hidden_channels: int = 32, num_classes: int = 2, dropout: float = 0.2):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, hidden_channels)
        self.dropout = dropout
        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, num_classes),
        )

    def forward(self, x, edge_index, batch=None):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = self.conv1(x, edge_index)
        h = F.relu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        h = self.conv2(h, edge_index)
        h = F.relu(h)

        # Global pooling (mean + max concatenation)
        pool_mean = global_mean_pool(h, batch)
        pool_max = global_max_pool(h, batch)
        graph_repr = torch.cat([pool_mean, pool_max], dim=-1)

        logits = self.classifier(graph_repr)
        return logits


class TrajectoryGAT(nn.Module):
    """Component C Comparative Model: Graph Attention Network with edge attention."""

    def __init__(self, in_channels: int = 8, hidden_channels: int = 32, num_classes: int = 2, heads: int = 2, dropout: float = 0.2):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1)
        self.dropout = dropout
        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels, hidden_channels),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_channels, num_classes),
        )

    def forward(self, x, edge_index, batch=None):
        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        h = self.conv1(x, edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=self.dropout, training=self.training)

        h = self.conv2(h, edge_index)
        h = F.elu(h)

        graph_repr = global_mean_pool(h, batch)
        logits = self.classifier(graph_repr)
        return logits
