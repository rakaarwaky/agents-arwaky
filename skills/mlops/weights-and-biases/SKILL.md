---
name: weights-and-biases
description: "W&B: log ML experiments, sweeps, model registry, dashboards."
metadata:
  tags:
    - MLOps
    - Weights And Biases
    - WandB
    - Experiment Tracking
    - Hyperparameter Tuning
    - Model Registry
    - Collaboration
    - Real-Time Visualization
    - PyTorch
    - TensorFlow
    - HuggingFace
---

# Weights & Biases: ML Experiment Tracking & MLOps

## When to Use This Skill

Use Weights & Biases (W&B) when you need to:

- **Track ML experiments** with automatic metric logging
- **Visualize training** in real-time dashboards
- **Compare runs** across hyperparameters and configurations
- **Optimize hyperparameters** with automated sweeps
- **Manage model registry** with versioning and lineage
- **Collaborate on ML projects** with team workspaces
- **Track artifacts** (datasets, models, code) with lineage

**Users**: 200,000+ ML practitioners | **GitHub Stars**: 10.5k+ | **Integrations**: 100+

## Installation

```bash
# Install W&B
pip install wandb

# Login (creates API key)
wandb login

# Or set API key programmatically
export WANDB_API_KEY=your_api_key_here

```text

## Minimal Quick Start

```python
import wandb

run = wandb.init(project="my-project", config={"lr": 0.001, "epochs": 10})
for epoch in range(10):
    wandb.log({"epoch": epoch, "train/loss": train_loss, "val/loss": val_loss})
wandb.finish()

```text

Full PyTorch loop, config tracking, and metric patterns:
[references/tracking-basics.md](references/tracking-basics.md)

## Workflow Checklist

1. **Track a run** — `wandb.init` + `wandb.log` + `wandb.finish`.
   Details: [references/tracking-basics.md](references/tracking-basics.md#quick-start--core-concepts)
2. **Tune hyperparameters** — define `sweep_config`, run `wandb.sweep` + `wandb.agent`.
   Details: [references/sweeps.md](references/sweeps.md)
3. **Version data/models** — `wandb.Artifact`, `log_artifact`, model registry aliases.
   Details: [references/artifacts.md](references/artifacts.md)
4. **Integrate a framework** — HuggingFace `report_to="wandb"`, Lightning `WandbLogger`, Keras callbacks.
   Details: [references/integrations.md](references/integrations.md)
5. **Visualize + harden** — custom charts, tags/groups, offline mode.
   Details: [references/tracking-basics.md](references/tracking-basics.md#visualization--best-practices)

## Best Practices (summary)

1. Organize runs with tags, groups, and `job_type`.
2. Log system metrics, code version, and data splits — not just loss.
3. Use descriptive run names (`bert-base-lr0.001-bs32`), never `run1`.
4. Save final models and prediction tables as artifacts.
5. Use `WANDB_MODE=offline` on unstable connections, `wandb sync` later.

## Team & Pricing

- Share runs via URL; use team projects for shared artifacts/registry.
- **Free**: public projects, 100GB · **Academic**: free · **Teams**: $50/seat/mo · **Enterprise**: custom.

## Resources

- **Documentation**: https://docs.wandb.ai
- **GitHub**: https://github.com/wandb/wandb (10.5k+ stars)
- **Examples**: https://github.com/wandb/examples
- **Community**: https://wandb.ai/community
- **Discord**: https://wandb.me/discord

## References

| File | Read it when |
|------|--------------|
| `references/tracking-basics.md` | Quick-start loops, config/metric patterns, charts, best practices |
| `references/sweeps.md` | Comprehensive hyperparameter optimization guide |
| `references/artifacts.md` | Data and model versioning patterns |
| `references/integrations.md` | Framework-specific examples |
