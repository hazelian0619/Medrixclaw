# Machine Learning & AI Reference

Comprehensive guide for deep learning, time series analysis, Bayesian methods, and model interpretability.

## Table of Contents

1. [Deep Learning](#deep-learning)
2. [Classical ML](#classical-ml)
3. [Time Series](#time-series)
4. [Bayesian Methods](#bayesian-methods)
5. [Model Interpretability](#model-interpretability)
6. [Graph ML](#graph-ml)

---

## Deep Learning

### PyTorch Lightning

```python
# uv pip install pytorch-lightning torch

import pytorch_lightning as pl
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

class LitModel(pl.LightningModule):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.layer1 = nn.Linear(input_dim, hidden_dim)
        self.layer2 = nn.Linear(hidden_dim, output_dim)
        self.loss_fn = nn.CrossEntropyLoss()
    
    def forward(self, x):
        x = torch.relu(self.layer1(x))
        return self.layer2(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = self.loss_fn(y_hat, y)
        self.log("train_loss", loss)
        return loss
    
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# Train
model = LitModel(input_dim=100, hidden_dim=64, output_dim=10)
trainer = pl.Trainer(max_epochs=10, accelerator="auto")
trainer.fit(model, train_dataloader)
```

### Transformers (Hugging Face)

```python
# uv pip install transformers torch

from transformers import AutoModel, AutoTokenizer

# Load pretrained model
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Encode text
text = "Hello, world!"
inputs = tokenizer(text, return_tensors="pt")
outputs = model(**inputs)

# Fine-tuning
from transformers import AutoModelForSequenceClassification, Trainer, TrainingArguments

model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=16
)
trainer = Trainer(model=model, args=training_args, train_dataset=train_dataset)
trainer.train()
```

### Stable Baselines3 (RL)

```python
# uv pip install stable-baselines3 gymnasium

from stable_baselines3 import PPO, DQN, A2C
import gymnasium as gym

# Create environment
env = gym.make("CartPole-v1")

# Train agent
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# Evaluate
obs, _ = env.reset()
for _ in range(1000):
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

---

## Classical ML

### scikit-learn

```python
# uv pip install scikit-learn pandas numpy

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

import pandas as pd
import numpy as np

# Load data
X, y = load_data()

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Preprocess
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred))

# Cross-validation
scores = cross_val_score(model, X_train_scaled, y_train, cv=5)

# Hyperparameter tuning
param_grid = {'n_estimators': [50, 100, 200], 'max_depth': [None, 10, 20]}
grid_search = GridSearchCV(RandomForestClassifier(), param_grid, cv=5)
grid_search.fit(X_train_scaled, y_train)
```

### scikit-survival (Survival Analysis)

```python
# uv pip install scikit-survival

from sksurv.ensemble import RandomSurvivalForest
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.metrics import concordance_index_censored

# Prepare survival data
# y = structured array with (event, time)

# Train model
rsf = RandomSurvivalForest(n_estimators=100, random_state=42)
rsf.fit(X_train, y_train)

# Predict survival functions
surv_funcs = rsf.predict_survival_function(X_test)

# Evaluate
cindex = concordance_index_censored(y_test["event"], y_test["time"], rsf.predict(X_test))
```

---

## Time Series

### aeon (Time Series ML)

```python
# uv pip install aeon

from aeon.classification.distance_based import KNeighborsTimeSeriesClassifier
from aeon.classification.convolution_based import RocketClassifier
from aeon.clustering import TimeSeriesKMeans

# Classification
clf = KNeighborsTimeSeriesClassifier(distance="dtw")
clf.fit(X_train, y_train)

# ROCKET (state-of-the-art)
rocket = RocketClassifier(num_kernels=10000)
rocket.fit(X_train, y_train)
```

### TimesFM (Foundation Model)

```python
# uv pip install timesfm

import timesfm

# Load model
tfm = timesfm.TimesFm(
    context_len=512,
    horizon_len=128,
    input_patch_len=32,
    output_patch_len=128,
    num_layers=20,
    model_dims=1280,
)

# Forecast
forecast = tfm.forecast(time_series, freq="D")
```

### Statsmodels

```python
# uv pip install statsmodels

import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ARIMA
model = ARIMA(data, order=(1, 1, 1))
results = model.fit()
forecast = results.forecast(steps=10)

# SARIMAX (seasonal)
model = SARIMAX(data, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
results = model.fit()

# Decomposition
decomposition = sm.tsa.seasonal_decompose(data, model='additive')
```

---

## Bayesian Methods

### PyMC

```python
# uv pip install pymc arviz

import pymc as pm
import arviz as az
import numpy as np

# Define model
with pm.Model() as model:
    # Priors
    mu = pm.Normal("mu", mu=0, sigma=10)
    sigma = pm.HalfNormal("sigma", sigma=1)
    
    # Likelihood
    obs = pm.Normal("obs", mu=mu, sigma=sigma, observed=data)
    
    # Sample
    trace = pm.sample(2000, tune=1000, cores=4)

# Analyze results
az.plot_trace(trace)
az.summary(trace)
```

### Bayesian Workflow

```python
# Hierarchical model
with pm.Model() as hierarchical_model:
    # Hyperpriors
    mu_mu = pm.Normal("mu_mu", mu=0, sigma=10)
    sigma_mu = pm.HalfNormal("sigma_mu", sigma=5)
    
    # Group-level priors
    mu = pm.Normal("mu", mu=mu_mu, sigma=sigma_mu, shape=n_groups)
    
    # Observation-level
    sigma = pm.HalfNormal("sigma", sigma=1)
    obs = pm.Normal("obs", mu=mu[group_idx], sigma=sigma, observed=data)
    
    trace = pm.sample(2000)

# Model comparison
with pm.Model() as model_1:
    # ... define model
    trace_1 = pm.sample()

with pm.Model() as model_2:
    # ... define alternative model
    trace_2 = pm.sample()

# Compare
compare = az.compare({"model_1": trace_1, "model_2": trace_2})
```

---

## Model Interpretability

### SHAP

```python
# uv pip install shap

import shap

# Tree-based models
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Summary plot
shap.summary_plot(shap_values, X_test)

# Individual prediction
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])

# Deep learning
explainer = shap.DeepExplainer(model, X_train)
shap_values = explainer.shap_values(X_test)

# Kernel explainer (model-agnostic)
explainer = shap.KernelExplainer(model.predict, shap.kmeans(X_train, 10))
shap_values = explainer.shap_values(X_test)
```

### Feature Importance

```python
from sklearn.inspection import permutation_importance

# Permutation importance
result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)

# Plot
import matplotlib.pyplot as plt
plt.barh(feature_names, result.importances_mean)
plt.xlabel("Permutation Importance")
```

---

## Graph ML

### PyTorch Geometric

```python
# uv pip install torch-geometric

import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.loader import DataLoader

# Create graph
edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
x = torch.tensor([[-1], [0], [1]], dtype=torch.float)
data = Data(x=x, edge_index=edge_index)

# GCN model
class GCN(torch.nn.Module):
    def __init__(self, num_features, hidden_dim, num_classes):
        super().__init__()
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, num_classes)
    
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x

# Train
model = GCN(num_features=1, hidden_dim=16, num_classes=2)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

for epoch in range(200):
    optimizer.zero_grad()
    out = model(data)
    loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()
```

### NetworkX

```python
# uv pip install networkx

import networkx as nx
import matplotlib.pyplot as plt

# Create graph
G = nx.Graph()
G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4)])

# Analysis
print(nx.degree_centrality(G))
print(nx.betweenness_centrality(G))
print(nx.clustering(G))

# Shortest path
path = nx.shortest_path(G, source=1, target=4)

# Communities
communities = nx.community.greedy_modularity_communities(G)

# Visualization
nx.draw(G, with_labels=True)
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| pytorch-lightning | `uv pip install pytorch-lightning` | Deep learning framework |
| transformers | `uv pip install transformers` | NLP/Transformers |
| stable-baselines3 | `uv pip install stable-baselines3` | Reinforcement learning |
| scikit-learn | `uv pip install scikit-learn` | Classical ML |
| scikit-survival | `uv pip install scikit-survival` | Survival analysis |
| aeon | `uv pip install aeon` | Time series ML |
| timesfm | `uv pip install timesfm` | Foundation forecasting |
| pymc | `uv pip install pymc` | Bayesian inference |
| shap | `uv pip install shap` | Model interpretability |
| torch-geometric | `uv pip install torch-geometric` | Graph neural networks |
| networkx | `uv pip install networkx` | Graph analysis |
