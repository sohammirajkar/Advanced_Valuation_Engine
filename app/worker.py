from celery import Celery
from celery import Celery
import numpy as np
from numba import jit
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from app.models.valuation_models import (
    BlackScholesModel, BinomialTreeModel, ExoticOptionsModel, BondPricingModel
)
from app.utils.cache import cached_computation, cache

celery_app = Celery(
    "valuation_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(name="monte_carlo_task")
@cached_computation("monte_carlo", ttl=1800)  # Cache for 30 minutes
def monte_carlo_task(trials: int = 1000, S0: float = 100, r: float = 0.05, 
                    sigma: float = 0.2, T: float = 1.0, K: float = 100,
                    option_type: str = "call") -> Dict[str, Any]:
    """
    Optimized Monte Carlo simulation for option pricing
    Uses vectorized NumPy operations and Numba JIT compilation
    """
    start_time = time.time()
    
    # Generate random paths using vectorized operations
    dt = T / 252  # Daily steps
    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt)
    
    # Generate all random numbers at once
    np.random.seed(42)  # For reproducible results
    random_numbers = np.random.standard_normal((trials, 252))
    
    # Vectorized path generation
    log_returns = drift + diffusion * random_numbers
    log_prices = np.log(S0) + np.cumsum(log_returns, axis=1)
    final_prices = np.exp(log_prices[:, -1])
    
    # Calculate payoffs
    if option_type.lower() == "call":
        payoffs = np.maximum(final_prices - K, 0)
    else:
        payoffs = np.maximum(K - final_prices, 0)
    
    # Calculate statistics
    option_price = np.exp(-r * T) * np.mean(payoffs)
    std_error = np.exp(-r * T) * np.std(payoffs) / np.sqrt(trials)
    
    computation_time = time.time() - start_time
    
    return {
        "option_price": float(option_price),
        "std_error": float(std_error),
        "confidence_interval": [
            float(option_price - 1.96 * std_error),
            float(option_price + 1.96 * std_error)
        ],
        "final_prices_stats": {
            "mean": float(np.mean(final_prices)),
            "std": float(np.std(final_prices)),
            "min": float(np.min(final_prices)),
            "max": float(np.max(final_prices)),
            "percentiles": {
                "5th": float(np.percentile(final_prices, 5)),
                "25th": float(np.percentile(final_prices, 25)),
                "50th": float(np.percentile(final_prices, 50)),
                "75th": float(np.percentile(final_prices, 75)),
                "95th": float(np.percentile(final_prices, 95))
            }
        },
        "computation_time_seconds": computation_time,
        "trials": trials
    }


@celery_app.task(name="black_scholes_task")
@cached_computation("black_scholes", ttl=3600)  # Cache for 1 hour
def black_scholes_task(S: float, K: float, T: float, r: float, sigma: float,
                      option_type: str = "call", calculate_greeks: bool = True) -> Dict[str, Any]:
    """
    Black-Scholes option pricing with Greeks calculation
    """
    start_time = time.time()
    
    if option_type.lower() == "call":
        option_price = BlackScholesModel.european_call(S, K, T, r, sigma)
    else:
        option_price = BlackScholesModel.european_put(S, K, T, r, sigma)
    
    result = {
        "option_price": float(option_price),
        "parameters": {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, "type": option_type}
    }
    
    if calculate_greeks:
        greeks = BlackScholesModel.greeks(S, K, T, r, sigma, option_type)
        result["greeks"] = {k: float(v) for k, v in greeks.items()}
    
    result["computation_time_seconds"] = time.time() - start_time
    return result


@celery_app.task(name="binomial_tree_task")
@cached_computation("binomial_tree", ttl=3600)
def binomial_tree_task(S: float, K: float, T: float, r: float, sigma: float,
                      steps: int = 100, option_type: str = "call", 
                      american: bool = True) -> Dict[str, Any]:
    """
    Binomial tree option pricing
    """
    start_time = time.time()
    
    if american:
        option_price = BinomialTreeModel.american_option(S, K, T, r, sigma, steps, option_type)
    else:
        option_price = BinomialTreeModel.european_option(S, K, T, r, sigma, steps, option_type)
    
    result = {
        "option_price": float(option_price),
        "parameters": {
            "S": S, "K": K, "T": T, "r": r, "sigma": sigma, 
            "steps": steps, "type": option_type, "american": american
        },
        "computation_time_seconds": time.time() - start_time
    }
    
    return result


@celery_app.task(name="exotic_option_task")
@cached_computation("exotic_option", ttl=1800)
def exotic_option_task(option_class: str, S: float, K: float, T: float, r: float, 
                      sigma: float, **kwargs) -> Dict[str, Any]:
    """
    Exotic option pricing (Asian, Barrier, Lookback)
    """
    start_time = time.time()
    
    result: Dict[str, Any]
    
    if option_class.lower() == "asian":
        result = ExoticOptionsModel.asian_option(
            S, K, T, r, sigma,
            option_type=kwargs.get("option_type", "call"),
            average_type=kwargs.get("average_type", "arithmetic"),
            num_paths=kwargs.get("num_paths", 10000),
            steps=kwargs.get("steps", 252)
        )
    elif option_class.lower() == "barrier":
        result = ExoticOptionsModel.barrier_option(
            S, K, T, r, sigma,
            barrier=kwargs.get("barrier", 90),
            barrier_type=kwargs.get("barrier_type", "down_and_out"),
            option_type=kwargs.get("option_type", "call"),
            num_paths=kwargs.get("num_paths", 10000),
            steps=kwargs.get("steps", 252)
        )
    elif option_class.lower() == "lookback":
        result = ExoticOptionsModel.lookback_option(
            S, K, T, r, sigma,
            option_type=kwargs.get("option_type", "call"),
            lookback_type=kwargs.get("lookback_type", "floating"),
            num_paths=kwargs.get("num_paths", 10000),
            steps=kwargs.get("steps", 252)
        )
    else:
        raise ValueError(f"Unknown exotic option class: {option_class}")
    
    result["option_class"] = option_class
    result["parameters"] = {"S": S, "K": K, "T": T, "r": r, "sigma": sigma, **kwargs}
    result["computation_time_seconds"] = time.time() - start_time
    
    return result


@celery_app.task(name="bond_pricing_task")
@cached_computation("bond_pricing", ttl=3600)
def bond_pricing_task(face_value: float, coupon_rate: float, 
                     years_to_maturity: float, yield_to_maturity: Optional[float] = None,
                     price: Optional[float] = None, frequency: int = 2) -> Dict[str, Any]:
    """
    Bond pricing and yield calculations
    """
    start_time = time.time()
    
    result: Dict[str, Any] = {
        "parameters": {
            "face_value": face_value,
            "coupon_rate": coupon_rate,
            "years_to_maturity": years_to_maturity,
            "frequency": frequency
        }
    }
    
    if yield_to_maturity is not None:
        # Calculate bond price from yield
        bond_price = BondPricingModel.bond_price(
            face_value, coupon_rate, yield_to_maturity, years_to_maturity, frequency
        )
        duration_info = BondPricingModel.duration(
            face_value, coupon_rate, yield_to_maturity, years_to_maturity, frequency
        )
        
        result["bond_price"] = float(bond_price)
        result["yield_to_maturity"] = float(yield_to_maturity)
        result["macaulay_duration"] = float(duration_info["macaulay_duration"])
        result["modified_duration"] = float(duration_info["modified_duration"])
    
    elif price is not None:
        # Calculate yield from price
        ytm = BondPricingModel.bond_yield(
            price, face_value, coupon_rate, years_to_maturity, frequency
        )
        
        result["bond_price"] = float(price)
        result["yield_to_maturity"] = float(ytm)
    
    else:
        raise ValueError("Either yield_to_maturity or price must be provided")
    
    result["computation_time_seconds"] = time.time() - start_time
    return result


@celery_app.task(name="portfolio_monte_carlo_task")
@cached_computation("portfolio_monte_carlo", ttl=1800)
def portfolio_monte_carlo_task(weights: List[float], expected_returns: List[float],
                              cov_matrix: List[List[float]], initial_value: float = 100000,
                              time_horizon: float = 1.0, num_simulations: int = 10000) -> Dict[str, Any]:
    """
    Monte Carlo simulation for portfolio valuation
    """
    start_time = time.time()
    
    weights_array = np.array(weights)
    expected_returns_array = np.array(expected_returns)
    cov_matrix_array = np.array(cov_matrix)
    
    # Portfolio parameters
    portfolio_return = np.dot(weights_array, expected_returns_array)
    portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix_array, weights_array))
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # Monte Carlo simulation
    np.random.seed(42)
    random_returns = np.random.multivariate_normal(
        expected_returns_array, cov_matrix_array, num_simulations
    )
    
    portfolio_returns = np.dot(random_returns, weights_array)
    final_values = initial_value * (1 + portfolio_returns * time_horizon)
    
    # Calculate risk metrics
    var_95 = np.percentile(final_values, 5)
    var_99 = np.percentile(final_values, 1)
    cvar_95 = np.mean(final_values[final_values <= var_95])
    cvar_99 = np.mean(final_values[final_values <= var_99])
    
    result = {
        "portfolio_stats": {
            "expected_return": float(portfolio_return),
            "volatility": float(portfolio_volatility),
            "sharpe_ratio": float(portfolio_return / portfolio_volatility) if portfolio_volatility > 0 else 0
        },
        "simulation_results": {
            "mean_final_value": float(np.mean(final_values)),
            "std_final_value": float(np.std(final_values)),
            "min_value": float(np.min(final_values)),
            "max_value": float(np.max(final_values)),
            "percentiles": {
                "1st": float(np.percentile(final_values, 1)),
                "5th": float(np.percentile(final_values, 5)),
                "25th": float(np.percentile(final_values, 25)),
                "50th": float(np.percentile(final_values, 50)),
                "75th": float(np.percentile(final_values, 75)),
                "95th": float(np.percentile(final_values, 95)),
                "99th": float(np.percentile(final_values, 99))
            }
        },
        "risk_metrics": {
            "var_95": float(var_95),
            "var_99": float(var_99),
            "cvar_95": float(cvar_95),
            "cvar_99": float(cvar_99),
            "max_drawdown": float(initial_value - np.min(final_values))
        },
        "parameters": {
            "weights": weights_array.tolist(),
            "expected_returns": expected_returns_array.tolist(),
            "initial_value": initial_value,
            "time_horizon": time_horizon,
            "num_simulations": num_simulations
        },
        "computation_time_seconds": time.time() - start_time
    }
    
    return result
