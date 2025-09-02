from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.worker import (
    monte_carlo_task, black_scholes_task, binomial_tree_task, 
    exotic_option_task, bond_pricing_task, portfolio_monte_carlo_task
)

router = APIRouter()

@router.post("/montecarlo")
def run_montecarlo(background_tasks: BackgroundTasks, trials: int = 1000, 
                  S0: float = 100, r: float = 0.05, sigma: float = 0.2, 
                  T: float = 1.0, K: float = 100, option_type: str = "call"):
    """Run Monte Carlo simulation for option pricing"""
    task = monte_carlo_task.apply_async(args=[trials, S0, r, sigma, T, K, option_type])
    return {"task_id": task.id, "message": "Monte Carlo simulation started"}


@router.post("/black-scholes-async")
def run_black_scholes_async(background_tasks: BackgroundTasks, S: float, K: float, 
                           T: float, r: float, sigma: float, option_type: str = "call",
                           calculate_greeks: bool = True):
    """Run Black-Scholes calculation asynchronously"""
    task = black_scholes_task.apply_async(args=[S, K, T, r, sigma, option_type, calculate_greeks])
    return {"task_id": task.id, "message": "Black-Scholes calculation started"}


@router.post("/binomial-tree-async")
def run_binomial_tree_async(background_tasks: BackgroundTasks, S: float, K: float,
                           T: float, r: float, sigma: float, steps: int = 100,
                           option_type: str = "call", american: bool = True):
    """Run Binomial Tree calculation asynchronously"""
    task = binomial_tree_task.apply_async(args=[S, K, T, r, sigma, steps, option_type, american])
    return {"task_id": task.id, "message": "Binomial Tree calculation started"}


@router.post("/exotic-option-async")
def run_exotic_option_async(background_tasks: BackgroundTasks, option_class: str,
                           S: float, K: float, T: float, r: float, sigma: float,
                           **kwargs):
    """Run Exotic Option calculation asynchronously"""
    task = exotic_option_task.apply_async(args=[option_class, S, K, T, r, sigma], kwargs=kwargs)
    return {"task_id": task.id, "message": f"{option_class.title()} option calculation started"}


@router.post("/bond-pricing-async")
def run_bond_pricing_async(background_tasks: BackgroundTasks, face_value: float,
                          coupon_rate: float, years_to_maturity: float,
                          yield_to_maturity: Optional[float] = None,
                          price: Optional[float] = None, frequency: int = 2):
    """Run Bond pricing calculation asynchronously"""
    task = bond_pricing_task.apply_async(
        args=[face_value, coupon_rate, years_to_maturity, yield_to_maturity, price, frequency]
    )
    return {"task_id": task.id, "message": "Bond pricing calculation started"}


@router.post("/portfolio-monte-carlo-async")
def run_portfolio_monte_carlo_async(background_tasks: BackgroundTasks, weights: List[float],
                                   expected_returns: List[float], cov_matrix: List[List[float]],
                                   initial_value: float = 100000, time_horizon: float = 1.0,
                                   num_simulations: int = 10000):
    """Run Portfolio Monte Carlo simulation asynchronously"""
    task = portfolio_monte_carlo_task.apply_async(
        args=[weights, expected_returns, cov_matrix, initial_value, time_horizon, num_simulations]
    )
    return {"task_id": task.id, "message": "Portfolio Monte Carlo simulation started"}

@router.get("/status/{task_id}")
def check_status(task_id: str):
    """Check the status of any Celery task"""
    from app.worker import celery_app
    result = celery_app.AsyncResult(task_id)
    
    if result.ready():
        if result.successful():
            return {
                "status": "completed", 
                "result": result.result,
                "task_id": task_id
            }
        else:
            return {
                "status": "failed",
                "error": str(result.result),
                "task_id": task_id
            }
    else:
        return {
            "status": "pending",
            "task_id": task_id
        }


@router.get("/list-active")
def list_active_tasks():
    """List all active tasks"""
    from app.worker import celery_app
    active_tasks = celery_app.control.inspect().active()
    return {"active_tasks": active_tasks}


@router.delete("/cancel/{task_id}")
def cancel_task(task_id: str):
    """Cancel a running task"""
    from app.worker import celery_app
    celery_app.control.revoke(task_id, terminate=True)
    return {"message": f"Task {task_id} cancellation requested"}


@router.get("/cache-stats")
def get_cache_stats():
    """Get cache statistics"""
    from app.utils.cache import cache
    return cache.get_cache_stats()
