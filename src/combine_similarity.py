from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class CombineReport:
    alpha: float
    shape: Tuple[int, int]
    sem_minmax: Tuple[float, float]
    str_minmax: Tuple[float, float]
    comb_minmax: Tuple[float, float]


def combine_similarities(
    sim_str: np.ndarray,
    sim_sem: np.ndarray,
    alpha: float = 0.5,
    *,
    force_diagonal_one: bool = True
) -> tuple[np.ndarray, CombineReport]:
    """
    Combine structural and semantic similarities into a single similarity matrix:

        sim_comb = alpha * sim_str + (1 - alpha) * sim_sem

    alpha in [0,1]
      - alpha=1.0 => purely structural
      - alpha=0.0 => purely semantic
    """
    sim_str = np.asarray(sim_str, dtype=float)
    sim_sem = np.asarray(sim_sem, dtype=float)

    if sim_str.shape != sim_sem.shape:
        raise ValueError(f"Shape mismatch: sim_str={sim_str.shape} vs sim_sem={sim_sem.shape}")

    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be in [0, 1]")

    sim_comb = alpha * sim_str + (1.0 - alpha) * sim_sem

    # numeric safety
    sim_comb = np.nan_to_num(sim_comb, nan=0.0, posinf=1.0, neginf=0.0)
    sim_comb = np.clip(sim_comb, 0.0, 1.0)

    if force_diagonal_one:
        np.fill_diagonal(sim_comb, 1.0)

    report = CombineReport(
        alpha=alpha,
        shape=sim_comb.shape,
        sem_minmax=(float(sim_sem.min()), float(sim_sem.max())),
        str_minmax=(float(sim_str.min()), float(sim_str.max())),
        comb_minmax=(float(sim_comb.min()), float(sim_comb.max())),
    )
    return sim_comb, report


def similarity_to_distance(sim: np.ndarray) -> np.ndarray:
    """
    Convert similarity [0..1] to distance [0..1]:

        dist = 1 - sim

    Diagonal is forced to 0.
    """
    sim = np.asarray(sim, dtype=float)
    dist = 1.0 - sim
    dist = np.clip(dist, 0.0, 1.0)
    np.fill_diagonal(dist, 0.0)
    return dist
