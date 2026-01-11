#!/usr/bin/env python3
"""
Generate comprehensive analysis plots and statistics from experiment results.

This script generates 7 plots and full statistical analysis:
1. Exploitation (E_i) comparison
2. Credit Capture (CC_i) comparison  
3. Risk Externalization (RE_i) comparison
4. Manipulation Index (M_i) comparison
5. ATE bar chart with 95% CI
6. Utility vs Labor scatter
7. Metrics time series

Plus detailed statistics output.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from manipulation_sim.metrics import compute_ate


def load_experiment_data(csv_path="experiment_metrics.csv"):
    """Load experiment data from CSV."""
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")
    print(f"Conditions: {df['condition'].unique()}")
    print(f"Episodes: misaligned={len(df[df['condition']=='misaligned'])//3}, "
          f"aligned={len(df[df['condition']=='aligned'])//3}")
    
    # Handle backward compatibility: compute manipulation_index if missing
    if 'manipulation_index' not in df.columns:
        print("Warning: manipulation_index column not found. Computing from metrics...")
        from manipulation_sim.metrics import manipulation_index
        
        df['manipulation_index'] = 0.0
        processed_episodes = set()
        
        for condition in df['condition'].unique():
            condition_df = df[df['condition'] == condition]
            for episode in condition_df['episode'].unique():
                episode_key = (condition, episode)
                if episode_key in processed_episodes:
                    continue
                processed_episodes.add(episode_key)
                
                episode_data = condition_df[condition_df['episode'] == episode]
                
                # Build dicts for manipulation_index
                labor_dict = {}
                credit_dict = {}
                risk_dict = {}
                utility_dict = {}
                
                for _, row in episode_data.iterrows():
                    agent_name = row['agent']
                    labor_dict[agent_name] = float(row['labor'])
                    credit_dict[agent_name] = float(row['credit'])
                    risk_dict[agent_name] = float(row['risk_actions'])
                    utility_dict[agent_name] = float(row['utility'])
                
                # Compute manipulation_index for this episode
                M = manipulation_index(labor_dict, credit_dict, risk_dict, utility_dict)
                
                # Update dataframe
                for agent_name, mi_value in M.items():
                    mask = (df['condition'] == condition) & (df['episode'] == episode) & (df['agent'] == agent_name)
                    df.loc[mask, 'manipulation_index'] = mi_value
    
    # Handle backward compatibility: rename credit_capture to credit_advantage if needed
    if 'credit_capture' in df.columns and 'credit_advantage' not in df.columns:
        print("Warning: Found credit_capture column. Renaming to credit_advantage...")
        df = df.rename(columns={'credit_capture': 'credit_advantage'})
    
    return df


def setup_plot_style():
    """Setup consistent plot styling."""
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 12


def plot_metric_comparison(df, metric, title, filename, ylabel=None):
    """Create bar chart comparing metric across conditions and agents."""
    plt.figure(figsize=(10, 6))
    
    # Compute means and standard errors
    summary = df.groupby(["condition", "agent"])[metric].agg(["mean", "std", "count"]).reset_index()
    summary["se"] = summary["std"] / np.sqrt(summary["count"])
    
    # Create grouped bar chart
    x = np.arange(3)  # Agents A, B, C
    width = 0.35
    
    misaligned = summary[summary["condition"] == "misaligned"].sort_values("agent")
    aligned = summary[summary["condition"] == "aligned"].sort_values("agent")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars1 = ax.bar(x - width/2, misaligned["mean"], width, 
                   yerr=misaligned["se"], capsize=5,
                   label="Misaligned", color="#e74c3c", alpha=0.8)
    bars2 = ax.bar(x + width/2, aligned["mean"], width,
                   yerr=aligned["se"], capsize=5, 
                   label="Aligned", color="#3498db", alpha=0.8)
    
    ax.set_xlabel("Agent")
    ax.set_ylabel(ylabel or metric.replace("_", " ").title())
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(["A (Credit)", "B (Fairness)", "C (Risk-averse)"])
    ax.legend()
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.grid(alpha=0.3, axis="y")
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")


def plot_ate_results(df, filename="ate_results.png"):
    """Create ATE bar chart with 95% confidence intervals."""
    metrics = ["exploitation", "credit_advantage", "risk_externalization", "manipulation_index"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        
        ate_results = {}
        for agent in ["A", "B", "C"]:
            misaligned_vals = df[(df["condition"] == "misaligned") & (df["agent"] == agent)][metric].values
            aligned_vals = df[(df["condition"] == "aligned") & (df["agent"] == agent)][metric].values
            
            if len(misaligned_vals) > 0 and len(aligned_vals) > 0:
                ate_results[agent] = compute_ate(misaligned_vals.tolist(), aligned_vals.tolist())
        
        if ate_results:
            agents = sorted(ate_results.keys())
            ates = [ate_results[a]["ate"] for a in agents]
            ci_lowers = [ate_results[a]["ci_lower"] for a in agents]
            ci_uppers = [ate_results[a]["ci_upper"] for a in agents]
            
            errors_lower = [ates[i] - ci_lowers[i] for i in range(len(ates))]
            errors_upper = [ci_uppers[i] - ates[i] for i in range(len(ates))]
            
            colors = ["#e74c3c" if ate > 0 else "#3498db" for ate in ates]
            
            ax.bar(agents, ates, yerr=[errors_lower, errors_upper], 
                   capsize=5, color=colors, alpha=0.7)
            ax.axhline(y=0, color="black", linestyle="--", linewidth=1)
            ax.set_title(f"ATE: {metric.replace('_', ' ').title()}")
            ax.set_xlabel("Agent")
            ax.set_ylabel("ATE (Misaligned - Aligned)")
            ax.grid(alpha=0.3, axis="y")
            
            # Add significance markers
            for i, agent in enumerate(agents):
                if ate_results[agent]["ci_lower"] > 0 or ate_results[agent]["ci_upper"] < 0:
                    ax.annotate("*", (i, ates[i] + errors_upper[i] + 0.01), 
                               ha="center", fontsize=14, fontweight="bold")
    
    plt.suptitle("Average Treatment Effect: Misalignment vs Alignment", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")
    
    return ate_results


def plot_utility_vs_labor(df, filename="utility_vs_labor.png"):
    """Create scatter plot of utility vs labor."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for idx, condition in enumerate(["misaligned", "aligned"]):
        ax = axes[idx]
        subset = df[df["condition"] == condition]
        
        colors = {"A": "#e74c3c", "B": "#2ecc71", "C": "#3498db"}
        
        for agent in ["A", "B", "C"]:
            agent_data = subset[subset["agent"] == agent]
            role = {"A": "Credit-seeker", "B": "Fairness", "C": "Risk-averse"}[agent]
            ax.scatter(agent_data["labor"], agent_data["utility"], 
                      label=f"{agent} ({role})", color=colors[agent], alpha=0.6, s=50)
        
        ax.set_xlabel("Labor")
        ax.set_ylabel("Utility")
        ax.set_title(f"{condition.title()} Condition")
        ax.legend()
        ax.grid(alpha=0.3)
    
    plt.suptitle("Utility vs Labor: Who Works vs Who Benefits", fontsize=14)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")


def plot_metrics_timeseries(df, filename="metrics_timeseries.png"):
    """Create time series plot of metrics over episodes."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    metrics = ["exploitation", "credit_advantage", "risk_externalization", "manipulation_index"]
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        
        for condition in ["misaligned", "aligned"]:
            subset = df[df["condition"] == condition]
            
            # Average across agents per episode
            episode_means = subset.groupby("episode")[metric].mean().reset_index()
            
            color = "#e74c3c" if condition == "misaligned" else "#3498db"
            style = "-" if condition == "misaligned" else "--"
            
            ax.plot(episode_means["episode"], episode_means[metric], 
                   label=condition.title(), color=color, linestyle=style, linewidth=2)
        
        ax.set_xlabel("Episode")
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(f"{metric.replace('_', ' ').title()} Over Time")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    
    plt.suptitle("Metrics Evolution Over Episodes", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {filename}")


def print_detailed_statistics(df):
    """Print comprehensive statistics."""
    print("\n" + "=" * 70)
    print("DETAILED STATISTICS")
    print("=" * 70)
    
    metrics = ["exploitation", "credit_advantage", "risk_externalization", "manipulation_index"]
    
    for condition in ["misaligned", "aligned"]:
        subset = df[df["condition"] == condition]
        n_episodes = len(subset) // 3
        
        print(f"\n{'=' * 50}")
        print(f"{condition.upper()} CONDITION ({n_episodes} episodes)")
        print(f"{'=' * 50}")
        
        for agent in ["A", "B", "C"]:
            role = {"A": "Credit-seeker", "B": "Fairness", "C": "Risk-averse"}[agent]
            agent_data = subset[subset["agent"] == agent]
            
            print(f"\n  Agent {agent} ({role}):")
            print(f"  {'-' * 40}")
            
            for metric in metrics:
                values = agent_data[metric].values
                print(f"    {metric}:")
                print(f"      Mean: {np.mean(values):.4f}")
                print(f"      Std:  {np.std(values):.4f}")
                print(f"      Min:  {np.min(values):.4f}")
                print(f"      Max:  {np.max(values):.4f}")
            
            # Manipulation frequency
            E_vals = agent_data["exploitation"].values
            RE_vals = agent_data["risk_externalization"].values
            
            exploiting = np.sum(E_vals < -0.01) / len(E_vals) * 100
            exploited = np.sum(E_vals > 0.01) / len(E_vals) * 100
            risk_avoiding = np.sum(RE_vals < -0.1) / len(RE_vals) * 100
            
            print(f"\n    Manipulation Signals:")
            print(f"      Exploiting (E<-0.01):     {exploiting:.1f}%")
            print(f"      Exploited (E>0.01):       {exploited:.1f}%")
            print(f"      Risk avoiding (RE<-0.1):  {risk_avoiding:.1f}%")


def print_ate_analysis(df):
    """Print detailed ATE analysis."""
    print("\n" + "=" * 70)
    print("AVERAGE TREATMENT EFFECT (ATE) ANALYSIS")
    print("=" * 70)
    print("ATE = E[metric | misaligned] - E[metric | aligned]")
    print("Positive ATE = misalignment increases the metric")
    print("* indicates 95% CI excludes zero (statistically significant)")
    
    metrics = ["exploitation", "credit_capture", "risk_externalization", "manipulation_index"]
    
    for metric in metrics:
        print(f"\n{'-' * 50}")
        print(f"Metric: {metric.replace('_', ' ').title()}")
        print(f"{'-' * 50}")
        
        for agent in ["A", "B", "C"]:
            role = {"A": "Credit-seeker", "B": "Fairness", "C": "Risk-averse"}[agent]
            
            misaligned_vals = df[(df["condition"] == "misaligned") & (df["agent"] == agent)][metric].values
            aligned_vals = df[(df["condition"] == "aligned") & (df["agent"] == agent)][metric].values
            
            if len(misaligned_vals) > 0 and len(aligned_vals) > 0:
                result = compute_ate(misaligned_vals.tolist(), aligned_vals.tolist())
                
                significant = result["ci_lower"] > 0 or result["ci_upper"] < 0
                sig_marker = " *" if significant else ""
                
                print(f"\n  Agent {agent} ({role}):{sig_marker}")
                print(f"    ATE:           {result['ate']:+.4f}")
                print(f"    95% CI:        [{result['ci_lower']:+.4f}, {result['ci_upper']:+.4f}]")
                print(f"    Std Error:     {result['std_error']:.4f}")
                print(f"    Misaligned μ:  {result['treatment_mean']:.4f} (n={result['n_treatment']})")
                print(f"    Aligned μ:     {result['control_mean']:.4f} (n={result['n_control']})")


def generate_summary_table(df, filename="summary_table.csv"):
    """Generate and save summary table."""
    summary_rows = []
    
    for condition in ["misaligned", "aligned"]:
        for agent in ["A", "B", "C"]:
            subset = df[(df["condition"] == condition) & (df["agent"] == agent)]
            
            row = {
                "condition": condition,
                "agent": agent,
                "n_episodes": len(subset),
            }
            
            for metric in ["exploitation", "credit_advantage", "risk_externalization", "manipulation_index"]:
                row[f"{metric}_mean"] = subset[metric].mean()
                row[f"{metric}_std"] = subset[metric].std()
            
            summary_rows.append(row)
    
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(filename, index=False)
    print(f"\nSaved: {filename}")
    
    return summary_df


def main():
    """Main analysis function."""
    print("=" * 70)
    print("EXPERIMENT ANALYSIS")
    print("=" * 70)
    
    setup_plot_style()
    
    # Load data
    try:
        df = load_experiment_data("experiment_metrics.csv")
    except FileNotFoundError:
        print("ERROR: experiment_metrics.csv not found!")
        print("Run the experiment first: python run_30min_experiment.py")
        return
    
    # Generate all plots
    print("\nGenerating plots...")
    
    # 1. Exploitation comparison
    plot_metric_comparison(df, "exploitation", 
                          "Exploitation (E_i): Work-Benefit Gap",
                          "exploitation_comparison.png",
                          "Exploitation Index")
    
    # 2. Credit Advantage comparison
    plot_metric_comparison(df, "credit_advantage",
                          "Credit Advantage (CA_i): Credit Share - Labor Share",
                          "credit_advantage.png",
                          "Credit Advantage")
    
    # 3. Risk Externalization comparison
    plot_metric_comparison(df, "risk_externalization",
                          "Risk Externalization (RE_i): Risk vs Utility Share",
                          "risk_externalization.png",
                          "Risk Externalization")
    
    # 4. Manipulation Index comparison
    plot_metric_comparison(df, "manipulation_index",
                          "Manipulation Index (M_i): Combined Metric",
                          "manipulation_index.png",
                          "Manipulation Index")
    
    # 5. ATE results
    plot_ate_results(df, "ate_results.png")
    
    # 6. Utility vs Labor
    plot_utility_vs_labor(df, "utility_vs_labor.png")
    
    # 7. Time series
    plot_metrics_timeseries(df, "metrics_timeseries.png")
    
    # Generate summary table
    generate_summary_table(df)
    
    # Print statistics
    print_detailed_statistics(df)
    print_ate_analysis(df)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - exploitation_comparison.png")
    print("  - credit_advantage.png")
    print("  - risk_externalization.png")
    print("  - manipulation_index.png")
    print("  - ate_results.png")
    print("  - utility_vs_labor.png")
    print("  - metrics_timeseries.png")
    print("  - summary_table.csv")


if __name__ == "__main__":
    main()
