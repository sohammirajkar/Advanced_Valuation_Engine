from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import numpy as np
from app.models.valuation_models import (
    BlackScholesModel, BinomialTreeModel, ExoticOptionsModel, BondPricingModel
)

router = APIRouter()

class CashFlowRequest(BaseModel):
    cash_flows: List[float]
    discount_rate: float


class OptionRequest(BaseModel):
    S: float = Field(..., description="Current stock price")
    K: float = Field(..., description="Strike price")
    T: float = Field(..., description="Time to expiration (years)")
    r: float = Field(..., description="Risk-free rate")
    sigma: float = Field(..., description="Volatility")
    option_type: str = Field("call", description="Option type: 'call' or 'put'")


class BinomialTreeRequest(OptionRequest):
    steps: int = Field(100, description="Number of steps in binomial tree")
    american: bool = Field(True, description="True for American, False for European")


class ExoticOptionRequest(OptionRequest):
    option_class: str = Field(..., description="Exotic option type: 'asian', 'barrier', 'lookback'")
    barrier: Optional[float] = Field(None, description="Barrier level (for barrier options)")
    barrier_type: Optional[str] = Field("down_and_out", description="Barrier type")
    average_type: Optional[str] = Field("arithmetic", description="Average type for Asian options")
    lookback_type: Optional[str] = Field("floating", description="Lookback type")
    num_paths: Optional[int] = Field(10000, description="Number of Monte Carlo paths")
    steps: Optional[int] = Field(252, description="Number of time steps")


class BondRequest(BaseModel):
    face_value: float = Field(..., description="Face value of the bond")
    coupon_rate: float = Field(..., description="Annual coupon rate")
    years_to_maturity: float = Field(..., description="Years to maturity")
    yield_to_maturity: Optional[float] = Field(None, description="Yield to maturity")
    price: Optional[float] = Field(None, description="Bond price")
    frequency: int = Field(2, description="Coupon payment frequency per year")


class PortfolioRequest(BaseModel):
    weights: List[float] = Field(..., description="Portfolio weights")
    expected_returns: List[float] = Field(..., description="Expected returns for each asset")
    cov_matrix: List[List[float]] = Field(..., description="Covariance matrix")
    initial_value: float = Field(100000, description="Initial portfolio value")
    time_horizon: float = Field(1.0, description="Time horizon in years")
    num_simulations: int = Field(10000, description="Number of Monte Carlo simulations")


class ImpliedVolatilityRequest(BaseModel):
    option_price: float = Field(..., description="Market price of the option")
    S: float = Field(..., description="Current stock price")
    K: float = Field(..., description="Strike price")
    T: float = Field(..., description="Time to expiration (years)")
    r: float = Field(..., description="Risk-free rate")
    option_type: str = Field("call", description="Option type: 'call' or 'put'")

@router.post("/npv")
def calculate_npv(data: CashFlowRequest):
    """Calculate Net Present Value of cash flows"""
    npv = sum(cf / ((1 + data.discount_rate) ** i) for i, cf in enumerate(data.cash_flows, start=1))
    return {"npv": npv}


@router.post("/black-scholes")
def black_scholes_pricing(data: OptionRequest) -> Dict[str, Any]:
    """Black-Scholes option pricing with Greeks"""
    if data.option_type.lower() == "call":
        option_price = BlackScholesModel.european_call(data.S, data.K, data.T, data.r, data.sigma)
    else:
        option_price = BlackScholesModel.european_put(data.S, data.K, data.T, data.r, data.sigma)
    
    greeks = BlackScholesModel.greeks(data.S, data.K, data.T, data.r, data.sigma, data.option_type)
    
    return {
        "option_price": option_price,
        "greeks": greeks,
        "model": "Black-Scholes",
        "parameters": data.dict()
    }


@router.post("/binomial-tree")
def binomial_tree_pricing(data: BinomialTreeRequest) -> Dict[str, Any]:
    """Binomial tree option pricing (American/European)"""
    if data.american:
        option_price = BinomialTreeModel.american_option(
            data.S, data.K, data.T, data.r, data.sigma, data.steps, data.option_type
        )
    else:
        option_price = BinomialTreeModel.european_option(
            data.S, data.K, data.T, data.r, data.sigma, data.steps, data.option_type
        )
    
    return {
        "option_price": option_price,
        "model": "Binomial Tree",
        "american": data.american,
        "steps": data.steps,
        "parameters": data.dict()
    }


@router.post("/exotic-options")
def exotic_option_pricing(data: ExoticOptionRequest) -> Dict[str, Any]:
    """Pricing for exotic options (Asian, Barrier, Lookback)"""
    kwargs = {
        "option_type": data.option_type,
        "num_paths": data.num_paths,
        "steps": data.steps
    }
    
    if data.option_class.lower() == "asian":
        kwargs["average_type"] = data.average_type
        result = ExoticOptionsModel.asian_option(
            data.S, data.K, data.T, data.r, data.sigma, **kwargs
        )
    elif data.option_class.lower() == "barrier":
        if data.barrier is None:
            return {"error": "Barrier level is required for barrier options"}
        kwargs.update({"barrier": data.barrier, "barrier_type": data.barrier_type})
        result = ExoticOptionsModel.barrier_option(
            data.S, data.K, data.T, data.r, data.sigma, **kwargs
        )
    elif data.option_class.lower() == "lookback":
        kwargs["lookback_type"] = data.lookback_type
        result = ExoticOptionsModel.lookback_option(
            data.S, data.K, data.T, data.r, data.sigma, **kwargs
        )
    else:
        return {"error": f"Unknown exotic option class: {data.option_class}"}
    
    # Type cast to ensure proper type inference
    result_dict: Dict[str, Any] = dict(result)
    result_dict["model"] = f"Monte Carlo - {data.option_class.title()} Option"
    result_dict["parameters"] = data.dict()
    return result_dict


@router.post("/bond-pricing")
def bond_pricing(data: BondRequest) -> Dict[str, Any]:
    """Bond pricing and yield calculations"""
    if data.yield_to_maturity is not None:
        # Calculate bond price from yield
        bond_price = BondPricingModel.bond_price(
            data.face_value, data.coupon_rate, data.yield_to_maturity, 
            data.years_to_maturity, data.frequency
        )
        duration_info = BondPricingModel.duration(
            data.face_value, data.coupon_rate, data.yield_to_maturity,
            data.years_to_maturity, data.frequency
        )
        
        return {
            "bond_price": bond_price,
            "yield_to_maturity": data.yield_to_maturity,
            "macaulay_duration": duration_info["macaulay_duration"],
            "modified_duration": duration_info["modified_duration"],
            "parameters": data.dict()
        }
    
    elif data.price is not None:
        # Calculate yield from price
        ytm = BondPricingModel.bond_yield(
            data.price, data.face_value, data.coupon_rate,
            data.years_to_maturity, data.frequency
        )
        
        return {
            "bond_price": data.price,
            "yield_to_maturity": ytm,
            "parameters": data.dict()
        }
    
    else:
        return {"error": "Either yield_to_maturity or price must be provided"}


@router.post("/implied-volatility")
def calculate_implied_volatility(data: ImpliedVolatilityRequest) -> Dict[str, Any]:
    """Calculate implied volatility from option price"""
    iv = BlackScholesModel.implied_volatility(
        data.option_price, data.S, data.K, data.T, data.r, data.option_type
    )
    
    return {
        "implied_volatility": iv,
        "market_price": data.option_price,
        "model_price": BlackScholesModel.european_call(data.S, data.K, data.T, data.r, iv) 
                      if data.option_type.lower() == "call" 
                      else BlackScholesModel.european_put(data.S, data.K, data.T, data.r, iv),
        "parameters": data.dict()
    }


@router.get("/option-chain")
def generate_option_chain(S: float, T: float, r: float, sigma: float, 
                         K_min: Optional[float] = None, K_max: Optional[float] = None, 
                         K_step: float = 5.0) -> Dict[str, Any]:
    """Generate option chain with multiple strikes"""
    if K_min is None:
        K_min = S * 0.8
    if K_max is None:
        K_max = S * 1.2
    
    strikes = np.arange(K_min, K_max + K_step, K_step)
    
    option_chain = []
    for K in strikes:
        call_price = BlackScholesModel.european_call(S, K, T, r, sigma)
        put_price = BlackScholesModel.european_put(S, K, T, r, sigma)
        call_greeks = BlackScholesModel.greeks(S, K, T, r, sigma, "call")
        put_greeks = BlackScholesModel.greeks(S, K, T, r, sigma, "put")
        
        option_chain.append({
            "strike": float(K),
            "call_price": call_price,
            "put_price": put_price,
            "call_delta": call_greeks["delta"],
            "put_delta": put_greeks["delta"],
            "gamma": call_greeks["gamma"],  # Same for calls and puts
            "theta": call_greeks["theta"],
            "vega": call_greeks["vega"]     # Same for calls and puts
        })
    
    return {
        "option_chain": option_chain,
        "parameters": {
            "S": S, "T": T, "r": r, "sigma": sigma,
            "K_min": K_min, "K_max": K_max, "K_step": K_step
        }
    }


@router.get("/volatility-surface")
def generate_volatility_surface(S: float, r: float, base_vol: float = 0.2,
                               K_range: float = 0.4, T_max: float = 2.0) -> Dict[str, Any]:
    """Generate volatility surface data"""
    strikes = np.linspace(S * (1 - K_range/2), S * (1 + K_range/2), 10)
    times = np.linspace(0.1, T_max, 8)
    
    surface_data = []
    for T in times:
        for K in strikes:
            # Simple volatility smile model (for demonstration)
            moneyness = np.log(K / S)
            vol = base_vol * (1 + 0.1 * moneyness**2 + 0.05 * np.sqrt(T))
            
            call_price = BlackScholesModel.european_call(S, K, T, r, vol)
            put_price = BlackScholesModel.european_put(S, K, T, r, vol)
            
            surface_data.append({
                "strike": float(K),
                "time_to_expiry": float(T),
                "volatility": float(vol),
                "call_price": call_price,
                "put_price": put_price,
                "moneyness": float(moneyness)
            })
    
    return {
        "volatility_surface": surface_data,
        "parameters": {
            "S": S, "r": r, "base_vol": base_vol,
            "K_range": K_range, "T_max": T_max
        }
    }
