"""
Analysis and plotting helpers for loading logs, computing stats, and visualization.

This module provides utilities for post-hoc analysis of simulation runs.
"""

import json
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from .simulate import load_run
from .metrics import (
    exploitation,
    credit_capture,
    risk_externalization,
    manipulation_index,
    compute_ate,
    compute_ate_by_agent,
)


def load_all_runs(pattern: str = "logs/*.json") -> List[Dict]:
    """
    Load all simulation runs matching a pattern.
    
    Args:
        pattern: Glob pattern for log files
    
    Returns:
        List of loaded run dicts
    """
    runs = []
    for fpath in glob.glob(pattern):
        try:
            with open(fpath, "r") as f:
                runs.append(json.load(f))
        except Exception as e:
            print(f"Error loading {fpath}: {e}")
    return runs


def extract_metrics_from_run(run: Dict) -> Dict[str, Dict[str, float]]:
    """
    Extract all metrics from a single run.
    
    Args:
        run: Run dict from load_run
    
    Returns:
        Dict mapping metric names to agent-wise values
    """
    # Get final state
    final_day = run["log"][-1]
    world_state = final_day["world"]
    
    # Extract agent states
    agents_data = world_state["agents"]
    labor = {name: data["labor"] for name, data in agents_data.items()}
    credit = {name: data["credit"] for name, data in agents_data.items()}
    risk_actions = {name: data["risk_actions"] for name, data in agents_data.items()}
    utility = run["final_rewards"]
    
    # Compute metrics
    E = exploitation(labor, utility)
    CC = credit_capture(credit, labor)
    RE = risk_externalization(risk_actions, utility)
    M = manipulation_index(labor, credit, risk_actions, utility)
    
    return {
        "exploitation": E,
        "credit_capture": CC,
        "risk_externalization": RE,
        "manipulation_index": M,
        "labor": labor,
        "credit": credit,
        "risk_actions": risk_actions,
        "utility": utility,
    }


def runs_to_dataframe(runs: List[Dict]) -> pd.DataFrame:
    """
    Convert list of runs to a pandas DataFrame for analysis.
    
    Args:
        runs: List of run dicts
    
    Returns:
        DataFrame with one row per agent per run
    """
    rows = []
    
    for run in runs:
        run_id = run.get("run_id", "unknown")
        metadata = run.get("metadata", {})
        aligned = metadata.get("aligned", False)
        allow_communication = metadata.get("allow_communication", True)
        
        # Extract metrics
        metrics = extract_metrics_from_run(run)
        
        # Create one row per agent
        for agent_name in metrics["labor"].keys():
            row = {
                "run_id": run_id,
                "aligned": aligned,
                "allow_communication": allow_communication,
                "agent": agent_name,
                "labor": metrics["labor"][agent_name],
                "credit": metrics["credit"][agent_name],
                "risk_actions": metrics["risk_actions"][agent_name],
                "utility": metrics["utility"][agent_name],
                "exploitation": metrics["exploitation"][agent_name],
                "credit_capture": metrics["credit_capture"][agent_name],
                "risk_externalization": metrics["risk_externalization"][agent_name],
                "manipulation_index": metrics["manipulation_index"][agent_name],
            }
            rows.append(row)
    
    return pd.DataFrame(rows)


def plot_utility_vs_labor(
    df: pd.DataFrame,
    aligned: Optional[bool] = None,
    save_path: Optional[str] = None,
):
    """
    Plot utility vs labor scatter plot.
    
    Args:
        df: DataFrame from runs_to_dataframe
        aligned: If provided, filter to this condition
        save_path: Optional path to save figure
    """
    if aligned is not None:
        df_plot = df[df["aligned"] == aligned].copy()
        title_suffix = f" (aligned={aligned})"
    else:
        df_plot = df.copy()
        title_suffix = ""
    
    plt.figure(figsize=(10, 6))
    
    for agent in df_plot["agent"].unique():
        agent_data = df_plot[df_plot["agent"] == agent]
        plt.scatter(
            agent_data["labor"],
            agent_data["utility"],
            label=agent,
            alpha=0.6,
            s=50,
        )
    
    plt.title(f"Utility vs Labor{title_suffix}")
    plt.xlabel("Labor")
    plt.ylabel("Utility")
    plt.legend()
    plt.grid(alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    
    plt.show()


def plot_metrics_comparison(
    df: pd.DataFrame,
    metric: str = "exploitation",
    save_path: Optional[str] = None,
):
    """
    Plot metric comparison across aligned/misaligned conditions.
    
    Args:
        df: DataFrame from runs_to_dataframe
        metric: Metric name to plot
        save_path: Optional path to save figure
    """
    # Group by condition and agent
    df_group = df.groupby(["aligned", "agent"])[metric].mean().reset_index()
    
    # Pivot for easier plotting
    df_pivot = df_group.pivot(index="agent", columns="aligned", values=metric)
    
    df_pivot.plot(kind="bar", figsize=(10, 6))
    plt.title(f"{metric.replace('_', ' ').title()} by Agent and Condition")
    plt.xlabel("Agent")
    plt.ylabel(metric.replace("_", " ").title())
    plt.legend(title="Aligned", labels=["Misaligned", "Aligned"])
    plt.xticks(rotation=0)
    plt.grid(alpha=0.3, axis="y")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    
    plt.show()


def plot_ate_bars(
    ate_results: Dict[str, Dict[str, float]],
    metric_name: str = "Exploitation",
    save_path: Optional[str] = None,
):
    """
    Plot Average Treatment Effect as bar chart with error bars.
    
    Args:
        ate_results: Dict from compute_ate_by_agent
        metric_name: Name of metric for labeling
        save_path: Optional path to save figure
    """
    agents = sorted(ate_results.keys())
    ates = [ate_results[agent]["ate"] for agent in agents]
    ci_lowers = [ate_results[agent]["ci_lower"] for agent in agents]
    ci_uppers = [ate_results[agent]["ci_upper"] for agent in agents]
    
    errors_lower = [ates[i] - ci_lowers[i] for i in range(len(ates))]
    errors_upper = [ci_uppers[i] - ates[i] for i in range(len(ates))]
    
    plt.figure(figsize=(10, 6))
    plt.bar(agents, ates, yerr=[errors_lower, errors_upper], capsize=5, alpha=0.7)
    plt.axhline(y=0, color="r", linestyle="--", alpha=0.5, label="No effect")
    plt.title(f"Average Treatment Effect: {metric_name}")
    plt.xlabel("Agent")
    plt.ylabel(f"ATE: {metric_name}")
    plt.legend()
    plt.grid(alpha=0.3, axis="y")
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    
    plt.show()


def print_summary_table(df: pd.DataFrame):
    """
    Print summary statistics table.
    
    Args:
        df: DataFrame from runs_to_dataframe
    """
    metrics = ["exploitation", "credit_capture", "risk_externalization", "manipulation_index"]
    
    summary = df.groupby(["aligned", "agent"])[metrics].mean().reset_index()
    summary = summary.round(3)
    
    print("\n=== Summary Statistics ===")
    print(summary.to_string(index=False))
    print()


def compute_and_print_ate(df: pd.DataFrame, metric: str = "exploitation"):
    """
    Compute and print ATE results for a given metric.
    
    Args:
        df: DataFrame from runs_to_dataframe
        metric: Metric name to analyze
    """
    # Group by run_id to get treatment/control pairs
    aligned_data = df[df["aligned"] == True].groupby("agent")[metric].apply(list).to_dict()
    misaligned_data = df[df["aligned"] == False].groupby("agent")[metric].apply(list).to_dict()
    
    print(f"\n=== ATE Analysis: {metric} ===")
    
    for agent in sorted(set(aligned_data.keys()) | set(misaligned_data.keys())):
        aligned_values = aligned_data.get(agent, [])
        misaligned_values = misaligned_data.get(agent, [])
        
        if aligned_values and misaligned_values:
            ate_result = compute_ate(misaligned_values, aligned_values)
            print(f"\n{agent}:")
            print(f"  ATE: {ate_result['ate']:.4f}")
            print(f"  95% CI: [{ate_result['ci_lower']:.4f}, {ate_result['ci_upper']:.4f}]")
            print(f"  Treatment mean: {ate_result['treatment_mean']:.4f}")
            print(f"  Control mean: {ate_result['control_mean']:.4f}")


# Set default plotting style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 11
