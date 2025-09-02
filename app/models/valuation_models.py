"""
Comprehensive valuation models for financial instruments
Includes Black-Scholes, Binomial Trees, and Exotic Options
"""

import numpy as np
import scipy.stats as stats
from scipy.optimize import brentq
from numba import jit
from typing import Dict, List, Optional, Union, Any
import math


class BlackScholesModel:
    """Black-Scholes option pricing model"""
    
    @staticmethod
    @jit(nopython=True)
    def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 parameter"""
        return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    @jit(nopython=True)
    def _d2(d1: float, sigma: float, T: float) -> float:
        """Calculate d2 parameter"""
        return d1 - sigma * np.sqrt(T)
    
    @classmethod
    def european_call(cls, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        European call option price using Black-Scholes formula
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
        """
        if T <= 0:
            return max(S - K, 0)
        
        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(d1, sigma, T)
        
        call_price = S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
        return max(call_price, 0)
    
    @classmethod
    def european_put(cls, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """European put option price using Black-Scholes formula"""
        if T <= 0:
            return max(K - S, 0)
        
        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(d1, sigma, T)
        
        put_price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
        return max(put_price, 0)
    
    @classmethod
    def greeks(cls, S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> Dict[str, Union[float, np.ndarray]]:
        """Calculate option Greeks"""
        if T <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
        
        d1 = cls._d1(S, K, T, r, sigma)
        d2 = cls._d2(d1, sigma, T)
        
        # Common calculations
        nd1 = stats.norm.cdf(d1)
        nd2 = stats.norm.cdf(d2)
        nprime_d1 = stats.norm.pdf(d1)
        
        if option_type.lower() == "call":
            delta = nd1
            rho = K * T * np.exp(-r * T) * nd2
            theta = (-S * nprime_d1 * sigma / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * nd2) / 365
        else:  # put
            delta = nd1 - 1
            rho = -K * T * np.exp(-r * T) * stats.norm.cdf(-d2)
            theta = (-S * nprime_d1 * sigma / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * stats.norm.cdf(-d2)) / 365
        
        gamma = nprime_d1 / (S * sigma * np.sqrt(T))
        vega = S * nprime_d1 * np.sqrt(T) / 100
        
        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "theta": float(theta),
            "vega": float(vega),
            "rho": float(rho)
        }
    
    @classmethod
    def implied_volatility(cls, option_price: float, S: float, K: float, T: float, 
                          r: float, option_type: str = "call") -> float:
        """Calculate implied volatility using Brent's method"""
        def objective(sigma):
            if option_type.lower() == "call":
                return cls.european_call(S, K, T, r, sigma) - option_price
            else:
                return cls.european_put(S, K, T, r, sigma) - option_price
        
        try:
            iv: float = brentq(objective, 0.001, 5.0, maxiter=100)  # type: ignore
            return iv
        except ValueError:
            return 0.0


class BinomialTreeModel:
    """Binomial tree model for American and European options"""
    
    @staticmethod
    @jit(nopython=True)
    def _build_tree(S: float, u: float, d: float, steps: int) -> np.ndarray:
        """Build price tree"""
        tree = np.zeros((steps + 1, steps + 1))
        for i in range(steps + 1):
            for j in range(i + 1):
                tree[j, i] = S * (u ** (i - j)) * (d ** j)
        return tree
    
    @classmethod
    def american_option(cls, S: float, K: float, T: float, r: float, sigma: float, 
                       steps: int = 100, option_type: str = "call") -> float:
        """American option pricing using binomial tree"""
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        
        # Build price tree
        price_tree = cls._build_tree(S, u, d, steps)
        
        # Initialize option values at expiration
        option_tree = np.zeros((steps + 1, steps + 1))
        for j in range(steps + 1):
            if option_type.lower() == "call":
                option_tree[j, steps] = max(price_tree[j, steps] - K, 0)
            else:
                option_tree[j, steps] = max(K - price_tree[j, steps], 0)
        
        # Backward induction
        for i in range(steps - 1, -1, -1):
            for j in range(i + 1):
                # European value
                european_value = np.exp(-r * dt) * (p * option_tree[j, i + 1] + 
                                                   (1 - p) * option_tree[j + 1, i + 1])
                
                # Early exercise value
                if option_type.lower() == "call":
                    exercise_value = max(price_tree[j, i] - K, 0)
                else:
                    exercise_value = max(K - price_tree[j, i], 0)
                
                # American option value
                option_tree[j, i] = max(european_value, exercise_value)
        
        return option_tree[0, 0]
    
    @classmethod
    def european_option(cls, S: float, K: float, T: float, r: float, sigma: float, 
                       steps: int = 100, option_type: str = "call") -> float:
        """European option pricing using binomial tree"""
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        
        # Build price tree
        price_tree = cls._build_tree(S, u, d, steps)
        
        # Initialize option values at expiration
        option_tree = np.zeros((steps + 1, steps + 1))
        for j in range(steps + 1):
            if option_type.lower() == "call":
                option_tree[j, steps] = max(price_tree[j, steps] - K, 0)
            else:
                option_tree[j, steps] = max(K - price_tree[j, steps], 0)
        
        # Backward induction (no early exercise)
        for i in range(steps - 1, -1, -1):
            for j in range(i + 1):
                option_tree[j, i] = np.exp(-r * dt) * (p * option_tree[j, i + 1] + 
                                                       (1 - p) * option_tree[j + 1, i + 1])
        
        return option_tree[0, 0]


class ExoticOptionsModel:
    """Pricing models for exotic options"""
    
    @staticmethod
    @jit(nopython=True)
    def _generate_paths(S0: float, T: float, r: float, sigma: float, 
                       steps: int, num_paths: int, seed: int = 42) -> np.ndarray:
        """Generate Monte Carlo price paths"""
        np.random.seed(seed)
        dt = T / steps
        drift = (r - 0.5 * sigma ** 2) * dt
        diffusion = sigma * np.sqrt(dt)
        
        paths = np.zeros((num_paths, steps + 1))
        paths[:, 0] = S0
        
        for i in range(1, steps + 1):
            z = np.random.standard_normal(num_paths)
            paths[:, i] = paths[:, i - 1] * np.exp(drift + diffusion * z)
        
        return paths
    
    @classmethod
    def asian_option(cls, S: float, K: float, T: float, r: float, sigma: float,
                    option_type: str = "call", average_type: str = "arithmetic",
                    num_paths: int = 10000, steps: int = 252) -> Dict[str, Union[float, List[float]]]:
        """Asian option pricing using Monte Carlo"""
        paths = cls._generate_paths(S, T, r, sigma, steps, num_paths)
        
        if average_type == "arithmetic":
            averages = np.mean(paths, axis=1)
        else:  # geometric
            averages = np.exp(np.mean(np.log(paths), axis=1))
        
        if option_type.lower() == "call":
            payoffs = np.maximum(averages - K, 0)
        else:
            payoffs = np.maximum(K - averages, 0)
        
        option_price = np.exp(-r * T) * np.mean(payoffs)
        std_error = np.exp(-r * T) * np.std(payoffs) / np.sqrt(num_paths)
        
        return {
            "price": option_price,
            "std_error": std_error,
            "confidence_interval": [option_price - 1.96 * std_error, 
                                   option_price + 1.96 * std_error]
        }
    
    @classmethod
    def barrier_option(cls, S: float, K: float, T: float, r: float, sigma: float,
                      barrier: float, barrier_type: str = "down_and_out",
                      option_type: str = "call", num_paths: int = 10000, 
                      steps: int = 252) -> Dict[str, Union[float, List[float]]]:
        """Barrier option pricing using Monte Carlo"""
        paths = cls._generate_paths(S, T, r, sigma, steps, num_paths)
        
        payoffs = np.zeros(num_paths)
        
        for i in range(num_paths):
            path = paths[i, :]
            final_price = path[-1]
            
            # Check barrier condition
            if barrier_type == "down_and_out":
                barrier_hit = np.any(path <= barrier)
            elif barrier_type == "up_and_out":
                barrier_hit = np.any(path >= barrier)
            elif barrier_type == "down_and_in":
                barrier_hit = np.any(path <= barrier)
            else:  # up_and_in
                barrier_hit = np.any(path >= barrier)
            
            # Calculate payoff
            if option_type.lower() == "call":
                intrinsic = max(final_price - K, 0)
            else:
                intrinsic = max(K - final_price, 0)
            
            # Apply barrier logic
            if "out" in barrier_type:
                payoffs[i] = intrinsic if not barrier_hit else 0
            else:  # "in" type
                payoffs[i] = intrinsic if barrier_hit else 0
        
        option_price = np.exp(-r * T) * np.mean(payoffs)
        std_error = np.exp(-r * T) * np.std(payoffs) / np.sqrt(num_paths)
        
        return {
            "price": option_price,
            "std_error": std_error,
            "confidence_interval": [option_price - 1.96 * std_error, 
                                   option_price + 1.96 * std_error]
        }
    
    @classmethod
    def lookback_option(cls, S: float, K: float, T: float, r: float, sigma: float,
                       option_type: str = "call", lookback_type: str = "floating",
                       num_paths: int = 10000, steps: int = 252) -> Dict[str, Union[float, List[float]]]:
        """Lookback option pricing using Monte Carlo"""
        paths = cls._generate_paths(S, T, r, sigma, steps, num_paths)
        
        payoffs = np.zeros(num_paths)
        
        for i in range(num_paths):
            path = paths[i, :]
            final_price = path[-1]
            max_price = np.max(path)
            min_price = np.min(path)
            
            if lookback_type == "floating":
                if option_type.lower() == "call":
                    payoffs[i] = max(final_price - min_price, 0)
                else:
                    payoffs[i] = max(max_price - final_price, 0)
            else:  # fixed
                if option_type.lower() == "call":
                    payoffs[i] = max(max_price - K, 0)
                else:
                    payoffs[i] = max(K - min_price, 0)
        
        option_price = np.exp(-r * T) * np.mean(payoffs)
        std_error = np.exp(-r * T) * np.std(payoffs) / np.sqrt(num_paths)
        
        return {
            "price": option_price,
            "std_error": std_error,
            "confidence_interval": [option_price - 1.96 * std_error, 
                                   option_price + 1.96 * std_error]
        }


class BondPricingModel:
    """Bond pricing and yield calculations"""
    
    @staticmethod
    def bond_price(face_value: float, coupon_rate: float, yield_to_maturity: float,
                  years_to_maturity: float, frequency: int = 2) -> float:
        """Calculate bond price given yield"""
        periods = int(years_to_maturity * frequency)
        coupon_payment = face_value * coupon_rate / frequency
        period_yield = yield_to_maturity / frequency
        
        if period_yield == 0:
            return face_value + coupon_payment * periods
        
        pv_coupons = coupon_payment * (1 - (1 + period_yield) ** -periods) / period_yield
        pv_face_value = face_value / (1 + period_yield) ** periods
        
        return pv_coupons + pv_face_value
    
    @staticmethod
    def bond_yield(price: float, face_value: float, coupon_rate: float,
                  years_to_maturity: float, frequency: int = 2) -> float:
        """Calculate yield to maturity given bond price"""
        def objective(y):
            return BondPricingModel.bond_price(face_value, coupon_rate, y, 
                                             years_to_maturity, frequency) - price
        
        try:
            ytm: float = brentq(objective, 0.001, 1.0, maxiter=100)  # type: ignore
            return ytm
        except ValueError:
            return 0.0
    
    @staticmethod
    def duration(face_value: float, coupon_rate: float, yield_to_maturity: float,
                years_to_maturity: float, frequency: int = 2) -> Dict[str, float]:
        """Calculate Macaulay and Modified duration"""
        periods = int(years_to_maturity * frequency)
        coupon_payment = face_value * coupon_rate / frequency
        period_yield = yield_to_maturity / frequency
        
        present_values = []
        weighted_times = []
        
        # Calculate present values and weighted times
        for t in range(1, periods + 1):
            if t == periods:
                cf = coupon_payment + face_value
            else:
                cf = coupon_payment
            
            pv = cf / (1 + period_yield) ** t
            present_values.append(pv)
            weighted_times.append(pv * t / frequency)
        
        bond_price = sum(present_values)
        macaulay_duration = sum(weighted_times) / bond_price
        modified_duration = macaulay_duration / (1 + yield_to_maturity / frequency)
        
        return {
            "macaulay_duration": macaulay_duration,
            "modified_duration": modified_duration,
            "bond_price": bond_price
        }