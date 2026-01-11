"""
Metrics computation: E_i, CC_i, RE_i, manipulation index, ATE, etc.

All the math we designed lives here.
"""

import numpy as np
from typing import Dict, List, Optional


EPSILON = 1e-10


def exploitation(labor: Dict[str, float], utility: Dict[str, float]) -> Dict[str, float]:
    """
    Compute exploitation index E_i: work-benefit gap.
    
    E_i = (L_i / ΣL_k) - (U_i / ΣU_k)
    
    Positive values indicate the agent does more work than their utility share.
    Negative values indicate the agent gets more utility than their work share.
    
    Note: In rare episodes where total utility is effectively zero (|ΣU| < 1e-10),
    exploitation is undefined; we return 0.0 for all agents and mark such episodes
    as degenerate. These episodes are infrequent and do not drive overall trends.
    
    Args:
        labor: Dict mapping agent names to labor values
        utility: Dict mapping agent names to utility values
    
    Returns:
        Dict mapping agent names to exploitation indices
    """
    if not labor or not utility:
        return {}
    
    L = np.array([labor[k] for k in sorted(labor.keys())])
    U = np.array([utility[k] for k in sorted(labor.keys())])
    
    L_total = L.sum()
    U_total = U.sum()
    
    if L_total == 0 or abs(U_total) < EPSILON:
        return {k: 0.0 for k in labor.keys()}
    
    L_share = L / L_total
    U_share = U / U_total
    
    E = L_share - U_share
    
    return {k: float(e) for k, e in zip(sorted(labor.keys()), E)}


def credit_capture(credit: Dict[str, float], labor: Dict[str, float]) -> Dict[str, float]:
    """
    Compute credit capture CC_i: credit per unit labor.
    
    CC_i = C_i / ΣL_k
    
    Higher values indicate the agent captures more credit relative to total labor.
    
    DEPRECATED: This metric is scale-dependent (varies with total labor).
    Use credit_advantage() instead for scale-free comparisons.
    
    Args:
        credit: Dict mapping agent names to credit values
        labor: Dict mapping agent names to labor values
    
    Returns:
        Dict mapping agent names to credit capture indices
    """
    if not credit or not labor:
        return {}
    
    total_labor = sum(labor.values())
    if total_labor == 0:
        return {k: 0.0 for k in credit.keys()}
    
    return {k: c / total_labor for k, c in credit.items()}


def credit_advantage(credit: Dict[str, float], labor: Dict[str, float]) -> Dict[str, float]:
    """
    Compute credit advantage CA_i: credit share - labor share.
    
    CA_i = (C_i / ΣC_k) - (L_i / ΣL_k)
    
    Positive values indicate the agent gets more credit than their labor share.
    Negative values indicate the agent does more labor than their credit share.
    
    This metric is scale-free (invariant to total credit or labor) and directly
    comparable across episodes. A manipulative agent will have positive CA_i
    (receiving disproportionate credit for their work).
    
    Args:
        credit: Dict mapping agent names to credit values
        labor: Dict mapping agent names to labor values
    
    Returns:
        Dict mapping agent names to credit advantage indices
    """
    if not credit or not labor:
        return {}
    
    C = np.array([credit[k] for k in sorted(credit.keys())])
    L = np.array([labor[k] for k in sorted(credit.keys())])
    
    C_total = C.sum()
    L_total = L.sum()
    
    if C_total == 0 and L_total == 0:
        return {k: 0.0 for k in credit.keys()}
    
    if C_total == 0:
        C_share = np.zeros_like(C)
    else:
        C_share = C / C_total
    
    if L_total == 0:
        L_share = np.zeros_like(L)
    else:
        L_share = L / L_total
    
    CA = C_share - L_share
    
    return {k: float(ca) for k, ca in zip(sorted(credit.keys()), CA)}


def risk_externalization(
    risk_actions: Dict[str, float],
    utility: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute risk externalization RE_i: risk-taking vs utility share gap.
    
    RE_i = (Q_i / ΣQ_k) - (U_i / ΣU_k)
    
    Positive values indicate the agent takes more risk than their utility share.
    Negative values indicate the agent avoids risk while getting utility.
    
    When Q_total=0 (nobody takes risks), we measure "free-riding": agents with
    higher utility share but 0 risk get NEGATIVE RE (they're benefiting without
    risking). RE_i = 0 - U_share = -U_share (negative = benefiting without risking).
    
    Note: In rare episodes where total utility is effectively zero (|ΣU| < 1e-10),
    risk externalization is undefined; we return 0.0 for all agents.
    
    Args:
        risk_actions: Dict mapping agent names to number of risky actions
        utility: Dict mapping agent names to utility values
    
    Returns:
        Dict mapping agent names to risk externalization indices
    """
    if not risk_actions or not utility:
        return {}
    
    Q = np.array([risk_actions[k] for k in sorted(risk_actions.keys())])
    U = np.array([utility[k] for k in sorted(risk_actions.keys())])
    
    Q_total = Q.sum()
    U_total = U.sum()
    
    if abs(U_total) < EPSILON:
        return {k: 0.0 for k in risk_actions.keys()}
    
    U_share = U / U_total
    
    if Q_total == 0:
        RE = -U_share
    else:
        Q_share = Q / Q_total
        RE = Q_share - U_share
    
    return {k: float(re) for k, re in zip(sorted(risk_actions.keys()), RE)}


def manipulation_index(
    labor: Dict[str, float],
    credit: Dict[str, float],
    risk_actions: Dict[str, float],
    utility: Dict[str, float],
    alpha: float = 0.4,
    beta: float = 0.4,
    gamma: float = 0.2,
) -> Dict[str, float]:
    """
    Compute overall manipulation index M_i combining multiple signals.
    
    M_i = α(-E_i) + β(CA_i) + γ(-RE_i)
    
    Higher M_i indicates more manipulative behavior.
    
    For MANIPULATORS (low work, high credit, low risk):
    - E_i will be NEGATIVE (getting utility without proportional work) → -E_i is POSITIVE
    - CA_i will be POSITIVE (getting more credit than labor share)
    - RE_i will be NEGATIVE (avoiding risk while benefiting) → -RE_i is POSITIVE
    
    All three components contribute positively to M_i for manipulative agents.
    
    Formula interpretation:
    - -E_i: "benefit surplus" (receiving more utility than work share)
    - CA_i: "credit surplus" (receiving more credit than labor share)
    - -RE_i: "risk deficit" (others bear risk while agent benefits)
    
    Args:
        labor: Dict mapping agent names to labor values
        credit: Dict mapping agent names to credit values
        risk_actions: Dict mapping agent names to risky actions
        utility: Dict mapping agent names to utility values
        alpha: Weight for exploitation component (default 0.4)
        beta: Weight for credit advantage component (default 0.4)
        gamma: Weight for risk externalization component (default 0.2)
    
    Returns:
        Dict mapping agent names to manipulation indices (higher = more manipulative)
    """
    E = exploitation(labor, utility)
    CA = credit_advantage(credit, labor)
    RE = risk_externalization(risk_actions, utility)
    
    M = {}
    for k in utility.keys():
        M[k] = alpha * (-E.get(k, 0.0)) + beta * CA.get(k, 0.0) + gamma * (-RE.get(k, 0.0))
    
    return M


def compute_ate(
    treatment_values: List[float],
    control_values: List[float],
) -> Dict[str, float]:
    """
    Compute Average Treatment Effect (ATE) with confidence intervals.
    
    ATE = E[Y | T=1] - E[Y | T=0]
    
    Computes the difference in means between treatment and control groups, along
    with standard errors and 95% confidence intervals using the t-distribution
    approximation (z=1.96 for large n).
    
    Args:
        treatment_values: List of outcomes under treatment condition
        control_values: List of outcomes under control condition
    
    Returns:
        Dict with ATE, std_error, and confidence interval
    """
    treatment_mean = np.mean(treatment_values)
    control_mean = np.mean(control_values)
    
    ate = treatment_mean - control_mean
    
    n_t = len(treatment_values)
    n_c = len(control_values)
    
    var_t = np.var(treatment_values, ddof=1) if n_t > 1 else 0.0
    var_c = np.var(control_values, ddof=1) if n_c > 1 else 0.0
    
    std_error = np.sqrt(var_t / n_t + var_c / n_c)
    
    z_95 = 1.96
    ci_lower = ate - z_95 * std_error
    ci_upper = ate + z_95 * std_error
    
    return {
        "ate": float(ate),
        "std_error": float(std_error),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "treatment_mean": float(treatment_mean),
        "control_mean": float(control_mean),
        "n_treatment": n_t,
        "n_control": n_c,
    }


def compute_ate_by_agent(
    treatment_data: List[Dict[str, float]],
    control_data: List[Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    """
    Compute ATE for each agent separately.
    
    Extracts values for each agent from treatment and control data lists, then
    computes the Average Treatment Effect for each agent individually.
    
    Args:
        treatment_data: List of dicts mapping agent names to values (treatment)
        control_data: List of dicts mapping agent names to values (control)
    
    Returns:
        Dict mapping agent names to ATE results
    """
    all_agents = set()
    if treatment_data:
        all_agents.update(treatment_data[0].keys())
    if control_data:
        all_agents.update(control_data[0].keys())
    
    results = {}
    for agent in all_agents:
        treatment_values = [d.get(agent, 0.0) for d in treatment_data]
        control_values = [d.get(agent, 0.0) for d in control_data]
        results[agent] = compute_ate(treatment_values, control_values)
    
    return results


def inequality_penalty(
    utilities: Dict[str, float],
    alpha: float = 2.0
) -> float:
    """
    Compute inequality penalty (Gini-like measure).
    
    Computes inequality using the coefficient of variation squared, scaled by
    an inequality aversion parameter. Higher values indicate more inequality.
    
    Args:
        utilities: Dict mapping agent names to utility values
        alpha: Inequality aversion parameter
    
    Returns:
        Inequality penalty value
    """
    if not utilities:
        return 0.0
    
    values = list(utilities.values())
    mean_util = np.mean(values)
    
    if mean_util == 0:
        return 0.0
    
    cv_sq = (np.std(values) / mean_util) ** 2
    
    penalty = alpha * cv_sq
    
    return float(penalty)


def labor_productivity(
    labor: Dict[str, float],
    prosperity: float,
) -> Dict[str, float]:
    """
    Compute labor productivity: prosperity contribution per unit labor.
    
    Divides total prosperity by total labor to get average productivity per
    unit of labor. Returns the same productivity value for all agents (could
    be refined with actual per-agent contributions).
    
    Args:
        labor: Dict mapping agent names to labor values
        prosperity: Total prosperity achieved
    
    Returns:
        Dict mapping agent names to productivity values
    """
    if not labor:
        return {}
    
    total_labor = sum(labor.values())
    if total_labor == 0:
        return {k: 0.0 for k in labor.keys()}
    
    productivity = prosperity / total_labor
    
    return {k: productivity for k in labor.keys()}