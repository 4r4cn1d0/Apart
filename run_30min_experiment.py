#!/usr/bin/env python3
"""
30-Minute Experiment: Run both aligned and misaligned conditions.

This script runs episodes for 30 minutes total:
- 15 minutes: Misaligned incentives (treatment)
- 15 minutes: Aligned incentives (control)

This provides data for ATE (Average Treatment Effect) calculation.
"""

import time
import json
import sys
import random
from datetime import datetime
from collections import defaultdict
import pandas as pd
import numpy as np

from manipulation_sim import run_episode, config
from manipulation_sim.metrics import (
    exploitation,
    credit_advantage,
    risk_externalization,
    manipulation_index,
)


class ExperimentRunner:
    """Run experiments for both aligned and misaligned conditions."""
    
    def __init__(self, total_duration_minutes=30, rng_seed=42):
        self.total_duration_seconds = total_duration_minutes * 60
        self.half_duration = self.total_duration_seconds / 2
        self.rng = random.Random(rng_seed)
        
        # Results storage
        self.misaligned_results = []
        self.aligned_results = []
        self.all_metrics = []
        
        # Fallback tracking
        self.total_fallbacks = 0
        self.total_decisions = 0
        
        self.start_time = None
        self.end_time = None
    
    def compute_episode_metrics(self, log, rewards, aligned):
        """Compute metrics from a single episode."""
        final_day = log[-1]
        world_state = final_day["world"]
        
        labor = {name: data["labor"] for name, data in world_state["agents"].items()}
        credit_vals = {name: data["credit"] for name, data in world_state["agents"].items()}
        risk_actions = {name: data["risk_actions"] for name, data in world_state["agents"].items()}
        
        E = exploitation(labor, rewards)
        CA = credit_advantage(credit_vals, labor)
        RE = risk_externalization(risk_actions, rewards)
        M = manipulation_index(labor, credit_vals, risk_actions, rewards)
        
        return {
            "aligned": aligned,
            "labor": labor,
            "credit": credit_vals,
            "risk_actions": risk_actions,
            "utilities": rewards,
            "exploitation": E,
            "credit_advantage": CA,
            "risk_externalization": RE,
            "manipulation_index": M,
            "prosperity": world_state["prosperity"],
        }
    
    def run_condition(self, aligned: bool, duration_seconds: float):
        """Run episodes for a specific condition until duration is reached."""
        condition_name = "ALIGNED" if aligned else "MISALIGNED"
        results = []
        
        print(f"\n{'=' * 70}")
        print(f"STARTING {condition_name} CONDITION")
        print(f"Duration: {duration_seconds / 60:.1f} minutes")
        print(f"{'=' * 70}\n")
        
        condition_start = time.time()
        episode_num = 0
        
        while (time.time() - condition_start) < duration_seconds:
            episode_num += 1
            episode_start = time.time()
            
            # Run episode
            run_id = f"exp_{condition_name.lower()}_{episode_num}_{int(time.time())}"
            
            try:
                log, rewards = run_episode(
                    run_id=run_id,
                    aligned=aligned,
                    n_days=config.N_DAYS,
                    rng_seed=self.rng.randint(0, 1000000),
                    allow_communication=True,
                )
                
                # Compute metrics
                metrics = self.compute_episode_metrics(log, rewards, aligned)
                results.append(metrics)
                self.all_metrics.append(metrics)
                
                episode_duration = time.time() - episode_start
                elapsed = time.time() - condition_start
                remaining = duration_seconds - elapsed
                
                # Progress display
                print(f"[{condition_name}] Episode {episode_num} | "
                      f"Duration: {episode_duration:.1f}s | "
                      f"Elapsed: {elapsed/60:.1f}m | "
                      f"Remaining: {remaining/60:.1f}m")
                
                # Show sample metrics every 5 episodes
                if episode_num % 5 == 0:
                    print(f"  Prosperity: {metrics['prosperity']} | "
                          f"E(A)={metrics['exploitation']['A']:.3f} | "
                          f"M(A)={metrics['manipulation_index']['A']:.3f}")
                
            except Exception as e:
                print(f"  [Error in episode {episode_num}]: {e}")
                continue
            
            # Small delay between episodes
            time.sleep(0.2)
        
        print(f"\n{condition_name} complete: {episode_num} episodes in {duration_seconds/60:.1f} minutes")
        return results
    
    def run(self):
        """Run the full experiment."""
        print("=" * 70)
        print("30-MINUTE MANIPULATION EXPERIMENT")
        print("=" * 70)
        print(f"Total duration: {self.total_duration_seconds / 60:.0f} minutes")
        print(f"  - Misaligned: {self.half_duration / 60:.0f} minutes")
        print(f"  - Aligned: {self.half_duration / 60:.0f} minutes")
        print(f"Days per episode: {config.N_DAYS}")
        print(f"Conversation turns per day: {config.MAX_CONVERSATION_TURNS}")
        print("=" * 70)
        
        self.start_time = time.time()
        
        try:
            # Phase 1: Misaligned (treatment)
            self.misaligned_results = self.run_condition(
                aligned=False, 
                duration_seconds=self.half_duration
            )
            
            # Phase 2: Aligned (control)
            self.aligned_results = self.run_condition(
                aligned=True, 
                duration_seconds=self.half_duration
            )
            
            self.end_time = time.time()
            
            # Final summary
            total_duration = self.end_time - self.start_time
            print(f"\n{'=' * 70}")
            print("EXPERIMENT COMPLETE")
            print(f"{'=' * 70}")
            print(f"Total duration: {total_duration / 60:.1f} minutes")
            print(f"Misaligned episodes: {len(self.misaligned_results)}")
            print(f"Aligned episodes: {len(self.aligned_results)}")
            
            # Print fallback statistics
            if self.total_decisions > 0:
                percentage = (self.total_fallbacks / self.total_decisions) * 100
                print(f"Total LLM fallbacks: {self.total_fallbacks} ({percentage:.2f}% of decisions)")
            
            # Save results
            self.save_results()
            
            # Print quick summary
            self.print_summary()
            
        except KeyboardInterrupt:
            print(f"\n[Stopped by user]")
            self.end_time = time.time()
            self.save_results()
    
    def save_results(self):
        """Save results to JSON and CSV files."""
        # Save full JSON
        output = {
            "experiment_type": "30min_ate_comparison",
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time) if self.end_time and self.start_time else None,
            "n_misaligned": len(self.misaligned_results),
            "n_aligned": len(self.aligned_results),
            "misaligned_results": self.misaligned_results,
            "aligned_results": self.aligned_results,
        }
        
        with open("experiment_results.json", "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"\nSaved: experiment_results.json")
        
        # Save CSV for easy analysis
        rows = []
        for i, metrics in enumerate(self.misaligned_results):
            for name in ["A", "B", "C"]:
                rows.append({
                    "condition": "misaligned",
                    "episode": i + 1,
                    "agent": name,
                    "labor": metrics["labor"][name],
                    "credit": metrics["credit"][name],
                    "risk_actions": metrics["risk_actions"][name],
                    "utility": metrics["utilities"][name],
                    "exploitation": metrics["exploitation"][name],
                    "credit_advantage": metrics["credit_advantage"][name],
                    "risk_externalization": metrics["risk_externalization"][name],
                    "manipulation_index": metrics["manipulation_index"][name],
                    "prosperity": metrics["prosperity"],
                })
        
        for i, metrics in enumerate(self.aligned_results):
            for name in ["A", "B", "C"]:
                rows.append({
                    "condition": "aligned",
                    "episode": i + 1,
                    "agent": name,
                    "labor": metrics["labor"][name],
                    "credit": metrics["credit"][name],
                    "risk_actions": metrics["risk_actions"][name],
                    "utility": metrics["utilities"][name],
                    "exploitation": metrics["exploitation"][name],
                    "credit_advantage": metrics["credit_advantage"][name],
                    "risk_externalization": metrics["risk_externalization"][name],
                    "manipulation_index": metrics["manipulation_index"][name],
                    "prosperity": metrics["prosperity"],
                })
        
        df = pd.DataFrame(rows)
        df.to_csv("experiment_metrics.csv", index=False)
        print(f"Saved: experiment_metrics.csv")
    
    def print_summary(self):
        """Print quick summary statistics."""
        print(f"\n{'=' * 70}")
        print("QUICK SUMMARY")
        print(f"{'=' * 70}")
        
        for condition, results in [("MISALIGNED", self.misaligned_results), 
                                    ("ALIGNED", self.aligned_results)]:
            if not results:
                continue
                
            print(f"\n{condition} ({len(results)} episodes):")
            
            for name in ["A", "B", "C"]:
                role = {"A": "Credit-seeker", "B": "Fairness", "C": "Risk-averse"}[name]
                
                E_vals = [m["exploitation"][name] for m in results]
                M_vals = [m["manipulation_index"][name] for m in results]
                
                print(f"  {name} ({role}):")
                print(f"    E: mean={np.mean(E_vals):.4f}, std={np.std(E_vals):.4f}")
                print(f"    M: mean={np.mean(M_vals):.4f}, std={np.std(M_vals):.4f}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run 30-minute ATE experiment")
    parser.add_argument("--duration", type=int, default=30, help="Total duration in minutes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    runner = ExperimentRunner(
        total_duration_minutes=args.duration,
        rng_seed=args.seed
    )
    runner.run()


if __name__ == "__main__":
    main()
