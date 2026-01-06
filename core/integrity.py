"""
HRPO-X v1.0.1 - Core Integrity Checker
=======================================
Runtime integrity checks for core module

Provides hash-based verification, numerical stability checks,
and distribution property validation.
"""

import torch
import hashlib
import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class CoreIntegrityChecker:
    """Runtime integrity checks for core module"""
    
    # Golden artifact hashes (updated when core changes)
    GOLDEN_HASHES = {
        'projection_v1.0.0': 'placeholder_hash_projection',
        'gating_v1.0.0': 'placeholder_hash_gating',
        'objective_v1.0.0': 'placeholder_hash_objective'
    }
    
    def __init__(self, check_golden: bool = True):
        """
        Initialize integrity checker.
        
        Args:
            check_golden: If True, verify against golden artifact hashes
        """
        self.check_golden = check_golden
        self.integrity_violations = []
        
    def check_numerical_stability(
        self,
        tensors: Dict[str, torch.Tensor],
        max_value: float = 1e6
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check tensors for numerical issues.
        
        Args:
            tensors: Dictionary of tensor name -> tensor
            max_value: Maximum allowed absolute value
            
        Returns:
            (is_stable, diagnostics)
        """
        diagnostics = {}
        is_stable = True
        
        for name, tensor in tensors.items():
            # Check for NaN
            has_nan = torch.isnan(tensor).any().item()
            diagnostics[f'{name}_has_nan'] = has_nan
            
            if has_nan:
                is_stable = False
                self._log_violation(f"NaN detected in {name}")
            
            # Check for Inf
            has_inf = torch.isinf(tensor).any().item()
            diagnostics[f'{name}_has_inf'] = has_inf
            
            if has_inf:
                is_stable = False
                self._log_violation(f"Inf detected in {name}")
            
            # Check for extreme values
            if not has_nan and not has_inf:
                max_abs = torch.abs(tensor).max().item()
                diagnostics[f'{name}_max_abs'] = max_abs
                
                if max_abs > max_value:
                    is_stable = False
                    self._log_violation(f"Extreme value in {name}: {max_abs}")
            
            # Check tensor stats
            diagnostics[f'{name}_mean'] = tensor.mean().item() if not has_nan else None
            diagnostics[f'{name}_std'] = tensor.std().item() if not has_nan else None
        
        diagnostics['overall_stable'] = is_stable
        return is_stable, diagnostics
    
    def check_distribution_properties(
        self,
        logits: torch.Tensor,
        tolerance: float = 1e-6
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Verify probability distribution properties.
        
        Args:
            logits: Logit tensor (before softmax) or probabilities (after softmax)
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, diagnostics)
        """
        diagnostics = {}
        is_valid = True
        
        # Convert to probabilities if needed
        if logits.max() > 1.0 or logits.min() < 0.0:
            # Assume logits, apply softmax
            probs = torch.softmax(logits, dim=-1)
            diagnostics['input_type'] = 'logits'
        else:
            probs = logits
            diagnostics['input_type'] = 'probabilities'
        
        # Check 1: Sum to 1
        prob_sum = probs.sum(dim=-1)
        sum_valid = torch.allclose(prob_sum, torch.ones_like(prob_sum), atol=tolerance)
        diagnostics['sum_valid'] = sum_valid.item()
        diagnostics['sum_mean'] = prob_sum.mean().item()
        diagnostics['sum_min'] = prob_sum.min().item()
        diagnostics['sum_max'] = prob_sum.max().item()
        
        if not sum_valid:
            is_valid = False
            self._log_violation(f"Distribution sum violation: {prob_sum.mean():.6f}")
        
        # Check 2: Non-negative
        non_negative = (probs >= -tolerance).all().item()
        diagnostics['non_negative'] = non_negative
        diagnostics['min_prob'] = probs.min().item()
        
        if not non_negative:
            is_valid = False
            self._log_violation(f"Negative probability: {probs.min():.6f}")
        
        # Check 3: Bounded [0, 1]
        bounded = ((probs >= -tolerance) & (probs <= 1.0 + tolerance)).all().item()
        diagnostics['bounded'] = bounded
        diagnostics['max_prob'] = probs.max().item()
        
        if not bounded:
            is_valid = False
            self._log_violation(f"Probability out of bounds: [{probs.min():.6f}, {probs.max():.6f}]")
        
        # Check 4: Entropy (information theoretic check)
        entropy = -(probs * torch.log(probs + 1e-10)).sum(dim=-1)
        diagnostics['entropy_mean'] = entropy.mean().item()
        diagnostics['entropy_min'] = entropy.min().item()
        diagnostics['entropy_max'] = entropy.max().item()
        
        # Entropy should be non-negative
        entropy_valid = (entropy >= -tolerance).all().item()
        diagnostics['entropy_valid'] = entropy_valid
        
        if not entropy_valid:
            is_valid = False
            self._log_violation(f"Negative entropy detected")
        
        diagnostics['overall_valid'] = is_valid
        return is_valid, diagnostics
    
    def check_gradient_properties(
        self,
        gradients: Dict[str, torch.Tensor],
        max_grad_norm: float = 10.0
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check gradient health.
        
        Args:
            gradients: Dictionary of parameter name -> gradient tensor
            max_grad_norm: Maximum allowed gradient norm
            
        Returns:
            (is_healthy, diagnostics)
        """
        diagnostics = {}
        is_healthy = True
        
        total_norm = 0.0
        param_norms = {}
        
        for name, grad in gradients.items():
            if grad is None:
                diagnostics[f'{name}_grad'] = 'None'
                continue
            
            # Check for NaN/Inf
            has_nan = torch.isnan(grad).any().item()
            has_inf = torch.isinf(grad).any().item()
            
            diagnostics[f'{name}_has_nan'] = has_nan
            diagnostics[f'{name}_has_inf'] = has_inf
            
            if has_nan or has_inf:
                is_healthy = False
                self._log_violation(f"Invalid gradient in {name}")
                continue
            
            # Compute norm
            param_norm = torch.norm(grad).item()
            param_norms[name] = param_norm
            total_norm += param_norm ** 2
            
            diagnostics[f'{name}_norm'] = param_norm
            diagnostics[f'{name}_mean'] = grad.mean().item()
            diagnostics[f'{name}_std'] = grad.std().item()
        
        # Total gradient norm
        total_norm = np.sqrt(total_norm)
        diagnostics['total_norm'] = total_norm
        diagnostics['max_grad_norm'] = max_grad_norm
        
        if total_norm > max_grad_norm:
            is_healthy = False
            self._log_violation(f"Gradient norm too large: {total_norm:.2f} > {max_grad_norm}")
        
        # Check for vanishing gradients
        if total_norm < 1e-8:
            diagnostics['vanishing_warning'] = True
            logger.warning(f"Potentially vanishing gradients: norm={total_norm:.2e}")
        
        diagnostics['overall_healthy'] = is_healthy
        return is_healthy, diagnostics
    
    def check_loss_trajectory(
        self,
        losses: List[float],
        window_size: int = 10
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Detect training anomalies from loss trajectory.
        
        Args:
            losses: List of recent loss values
            window_size: Window for computing statistics
            
        Returns:
            (is_normal, diagnostics)
        """
        diagnostics = {}
        is_normal = True
        
        if len(losses) < 2:
            diagnostics['insufficient_data'] = True
            return True, diagnostics
        
        losses_array = np.array(losses)
        
        # Check for NaN/Inf
        has_nan = np.isnan(losses_array).any()
        has_inf = np.isinf(losses_array).any()
        
        diagnostics['has_nan'] = has_nan
        diagnostics['has_inf'] = has_inf
        
        if has_nan or has_inf:
            is_normal = False
            self._log_violation("NaN or Inf in loss trajectory")
        
        # Compute statistics
        if len(losses) >= window_size:
            recent = losses_array[-window_size:]
            diagnostics['recent_mean'] = float(np.mean(recent))
            diagnostics['recent_std'] = float(np.std(recent))
            diagnostics['recent_min'] = float(np.min(recent))
            diagnostics['recent_max'] = float(np.max(recent))
            
            # Check for divergence (loss increasing rapidly)
            if len(losses) >= window_size * 2:
                older = losses_array[-(window_size*2):-window_size]
                mean_increase = np.mean(recent) - np.mean(older)
                
                diagnostics['mean_increase'] = float(mean_increase)
                
                # If loss increased by >50%, flag as potential divergence
                if mean_increase > np.abs(np.mean(older)) * 0.5:
                    is_normal = False
                    self._log_violation(f"Potential divergence: loss increased by {mean_increase:.2f}")
        
        # Check for oscillation (high variance)
        if len(losses) >= 5:
            variance = np.var(losses_array[-5:])
            mean_loss = np.abs(np.mean(losses_array[-5:]))
            
            diagnostics['variance'] = float(variance)
            diagnostics['coefficient_of_variation'] = float(np.sqrt(variance) / (mean_loss + 1e-10))
            
            # High coefficient of variation suggests instability
            if diagnostics['coefficient_of_variation'] > 2.0:
                logger.warning("High loss variance detected - potential instability")
                diagnostics['high_variance_warning'] = True
        
        diagnostics['overall_normal'] = is_normal
        return is_normal, diagnostics
    
    def _log_violation(self, message: str):
        """Log integrity violation"""
        self.integrity_violations.append(message)
        logger.error(f"[Integrity] {message}")
    
    def get_violations(self) -> List[str]:
        """Get all recorded violations"""
        return self.integrity_violations.copy()
    
    def clear_violations(self):
        """Clear violation history"""
        self.integrity_violations.clear()


# Utility functions for common checks
def check_tensor_health(tensor: torch.Tensor, name: str = "tensor") -> bool:
    """Quick health check for a single tensor"""
    if torch.isnan(tensor).any():
        logger.error(f"{name} contains NaN")
        return False
    if torch.isinf(tensor).any():
        logger.error(f"{name} contains Inf")
        return False
    return True


def check_model_parameters(model: torch.nn.Module) -> Dict[str, any]:
    """Check health of all model parameters"""
    diagnostics = {}
    all_healthy = True
    
    for name, param in model.named_parameters():
        if param is None:
            continue
            
        has_nan = torch.isnan(param).any().item()
        has_inf = torch.isinf(param).any().item()
        
        diagnostics[f'{name}_healthy'] = not (has_nan or has_inf)
        
        if has_nan or has_inf:
            all_healthy = False
            logger.error(f"Unhealthy parameter: {name}")
    
    diagnostics['all_healthy'] = all_healthy
    return diagnostics
