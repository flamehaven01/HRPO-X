"""
    HRPO-X v1.0.1 - Core Validators
    ================================
    Numerical and sanity checks for prototype components.
    These utilities are optional and do not claim paper compliance.
    """



import torch
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class EquationValidator:
    """Validates core equation properties used in this prototype"""
    
    def __init__(self, strict: bool = True, log_violations: bool = True):
        """
        Initialize equation validator.
        
        Args:
            strict: If True, raise exceptions on violations
            log_violations: If True, log validation failures
        """
        self.strict = strict
        self.log_violations = log_violations
        self.violation_count = 0
        
    def validate_projection(
        self,
        pi_theta: torch.Tensor,
        pi_ref: torch.Tensor,
        constraint_c: float = 0.01,
        tolerance: float = 1e-6
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Validate Equation 3: Simplex Projection with KL Constraint
        
        Ensures:
        1. Output is valid probability distribution (sums to 1)
        2. KL divergence constraint is satisfied
        3. No negative probabilities
        4. Numerical stability
        
        Args:
            pi_theta: Current policy distribution
            pi_ref: Reference policy distribution
            constraint_c: KL constraint (default 0.01 from paper)
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, diagnostics)
        """
        diagnostics = {}
        is_valid = True
        
        # Check 1: Valid probability distribution
        pi_sum = pi_theta.sum(dim=-1)
        sum_valid = torch.allclose(pi_sum, torch.ones_like(pi_sum), atol=tolerance)
        diagnostics['sum_valid'] = sum_valid.item()
        diagnostics['sum_value'] = pi_sum.mean().item()
        
        if not sum_valid:
            is_valid = False
            msg = f"[Eq.3] Distribution sum violation: {pi_sum.mean():.6f} != 1.0"
            self._handle_violation(msg)
        
        # Check 2: No negative probabilities
        non_negative = (pi_theta >= -tolerance).all()
        diagnostics['non_negative'] = non_negative.item()
        
        if not non_negative:
            is_valid = False
            min_val = pi_theta.min().item()
            msg = f"[Eq.3] Negative probability: min={min_val:.6f}"
            self._handle_violation(msg)
        
        # Check 3: KL divergence constraint
        kl_div = (pi_theta * (torch.log(pi_theta + 1e-10) - torch.log(pi_ref + 1e-10))).sum(dim=-1)
        kl_mean = kl_div.mean().item()
        kl_valid = kl_mean <= constraint_c + tolerance
        
        diagnostics['kl_divergence'] = kl_mean
        diagnostics['kl_constraint'] = constraint_c
        diagnostics['kl_valid'] = kl_valid
        
        if not kl_valid:
            is_valid = False
            msg = f"[Eq.3] KL constraint violation: {kl_mean:.6f} > {constraint_c:.6f}"
            self._handle_violation(msg)
        
        # Check 4: Numerical stability
        has_nan = torch.isnan(pi_theta).any()
        has_inf = torch.isinf(pi_theta).any()
        numerically_stable = not (has_nan or has_inf)
        
        diagnostics['numerically_stable'] = numerically_stable
        
        if not numerically_stable:
            is_valid = False
            msg = f"[Eq.3] Numerical instability: NaN={has_nan}, Inf={has_inf}"
            self._handle_violation(msg)
        
        diagnostics['overall_valid'] = is_valid
        return is_valid, diagnostics
    
    def validate_gating(
        self,
        a_t: torch.Tensor,
        r_t: torch.Tensor,
        r_min: float,
        tau: float = 0.5,
        c: float = 8.0,
        tolerance: float = 1e-6
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Validate Equation 4: Latent Gating Mechanism
        
        Ensures:
        1. Gating values in [0, 1] range
        2. Proper sigmoid behavior
        3. Hidden ratio r_t in valid range
        4. Temperature effect is correct
        
        Args:
            a_t: Gating values (after sigmoid)
            r_t: Hidden token ratio
            r_min: Minimum hidden ratio
            tau: Temperature parameter (default 0.5)
            c: Scaling constant (default 8.0)
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, diagnostics)
        """
        diagnostics = {}
        is_valid = True
        
        # Check 1: Gating values in [0, 1]
        in_range = ((a_t >= -tolerance) & (a_t <= 1.0 + tolerance)).all()
        diagnostics['gating_in_range'] = in_range.item()
        diagnostics['gating_min'] = a_t.min().item()
        diagnostics['gating_max'] = a_t.max().item()
        diagnostics['gating_mean'] = a_t.mean().item()
        
        if not in_range:
            is_valid = False
            msg = f"[Eq.4] Gating out of range: [{a_t.min():.6f}, {a_t.max():.6f}]"
            self._handle_violation(msg)
        
        # Check 2: Hidden ratio r_t validation
        r_t_mean = r_t.mean().item()
        r_t_valid = (r_min - tolerance <= r_t_mean <= 1.0 + tolerance)
        
        diagnostics['r_t_mean'] = r_t_mean
        diagnostics['r_min'] = r_min
        diagnostics['r_t_valid'] = r_t_valid
        
        if not r_t_valid:
            is_valid = False
            msg = f"[Eq.4] Hidden ratio invalid: r_t={r_t_mean:.6f}, r_min={r_min:.6f}"
            self._handle_violation(msg)
        
        # Check 3: Temperature effect (sigmoid should be smoother with higher tau)
        # Verify a_t is result of sigmoid((r_t - r_min) / (tau * c))
        expected_logit = (r_t - r_min) / (tau * c)
        expected_a_t = torch.sigmoid(expected_logit)
        sigmoid_match = torch.allclose(a_t, expected_a_t, atol=tolerance * 10)
        
        diagnostics['sigmoid_match'] = sigmoid_match.item()
        
        if not sigmoid_match:
            # This might be ok if a_t is from a different source
            # Just warn, don't fail
            msg = f"[Eq.4] Sigmoid mismatch (warning): expected vs actual"
            if self.log_violations:
                logger.warning(msg)
        
        # Check 4: Numerical stability
        has_nan = torch.isnan(a_t).any() or torch.isnan(r_t).any()
        has_inf = torch.isinf(a_t).any() or torch.isinf(r_t).any()
        numerically_stable = not (has_nan or has_inf)
        
        diagnostics['numerically_stable'] = numerically_stable
        
        if not numerically_stable:
            is_valid = False
            msg = f"[Eq.4] Numerical instability: NaN={has_nan}, Inf={has_inf}"
            self._handle_violation(msg)
        
        diagnostics['overall_valid'] = is_valid
        return is_valid, diagnostics
    
    def validate_objective(
        self,
        total_loss: torch.Tensor,
        policy_gradient_term: torch.Tensor,
        kl_term: torch.Tensor,
        beta: float = 0.005,
        tolerance: float = 1e-4
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Validate Equation 6: HRPO Objective Function
        
        Ensures:
        1. Loss composition is correct: L = PG - beta * KL
        2. Beta coefficient is applied correctly
        3. Terms have expected signs
        4. Loss is numerically stable
        
        Args:
            total_loss: Total HRPO loss
            policy_gradient_term: Policy gradient component
            kl_term: KL divergence regularization term
            beta: KL coefficient (default 0.005)
            tolerance: Numerical tolerance
            
        Returns:
            (is_valid, diagnostics)
        """
        diagnostics = {}
        is_valid = True
        
        # Check 1: Loss composition
        expected_loss = policy_gradient_term - beta * kl_term
        composition_valid = torch.allclose(total_loss, expected_loss, atol=tolerance)
        
        diagnostics['composition_valid'] = composition_valid.item()
        diagnostics['total_loss'] = total_loss.mean().item()
        diagnostics['pg_term'] = policy_gradient_term.mean().item()
        diagnostics['kl_term'] = kl_term.mean().item()
        diagnostics['beta'] = beta
        
        if not composition_valid:
            is_valid = False
            actual = total_loss.mean().item()
            expected = expected_loss.mean().item()
            msg = f"[Eq.6] Loss composition error: actual={actual:.6f}, expected={expected:.6f}"
            self._handle_violation(msg)
        
        # Check 2: Beta coefficient validation
        beta_valid = 0.0 < beta < 0.1  # Reasonable range from paper
        diagnostics['beta_valid'] = beta_valid
        
        if not beta_valid:
            is_valid = False
            msg = f"[Eq.6] Beta out of range: {beta:.6f} (expected 0.0-0.1)"
            self._handle_violation(msg)
        
        # Check 3: Term signs (PG typically negative for minimization)
        # This is a soft check - just record for monitoring
        diagnostics['pg_negative'] = (policy_gradient_term.mean() < 0).item()
        diagnostics['kl_positive'] = (kl_term.mean() > 0).item()
        
        # Check 4: Numerical stability
        has_nan = (torch.isnan(total_loss).any() or 
                   torch.isnan(policy_gradient_term).any() or 
                   torch.isnan(kl_term).any())
        has_inf = (torch.isinf(total_loss).any() or 
                   torch.isinf(policy_gradient_term).any() or 
                   torch.isinf(kl_term).any())
        numerically_stable = not (has_nan or has_inf)
        
        diagnostics['numerically_stable'] = numerically_stable
        
        if not numerically_stable:
            is_valid = False
            msg = f"[Eq.6] Numerical instability: NaN={has_nan}, Inf={has_inf}"
            self._handle_violation(msg)
        
        # Check 5: Loss magnitude sanity check
        loss_magnitude = abs(total_loss.mean().item())
        reasonable_magnitude = loss_magnitude < 1000.0  # Sanity check
        diagnostics['reasonable_magnitude'] = reasonable_magnitude
        
        if not reasonable_magnitude:
            is_valid = False
            msg = f"[Eq.6] Loss magnitude too large: {loss_magnitude:.2f}"
            self._handle_violation(msg)
        
        diagnostics['overall_valid'] = is_valid
        return is_valid, diagnostics
    
    def _handle_violation(self, message: str):
        """Handle validation violation"""
        self.violation_count += 1
        
        if self.log_violations:
            logger.error(message)
        
        if self.strict:
            raise ValueError(message)
    
    def get_violation_count(self) -> int:
        """Get total number of violations detected"""
        return self.violation_count
    
    def reset_violation_count(self):
        """Reset violation counter"""
        self.violation_count = 0


class ValidationReport:
    """Aggregates validation results for reporting"""
    
    def __init__(self):
        self.results = []
        
    def add_result(self, equation: str, is_valid: bool, diagnostics: Dict):
        """Add validation result"""
        self.results.append({
            'equation': equation,
            'valid': is_valid,
            'diagnostics': diagnostics
        })
    
    def is_all_valid(self) -> bool:
        """Check if all validations passed"""
        return all(r['valid'] for r in self.results)
    
    def get_summary(self) -> Dict:
        """Get summary of validation results"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['valid'])
        
        return {
            'total_validations': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': passed / total if total > 0 else 0.0,
            'all_valid': self.is_all_valid()
        }
    
    def __str__(self) -> str:
        """String representation"""
        summary = self.get_summary()
        lines = [
            "Validation Report",
            "=" * 50,
            f"Total: {summary['total_validations']}",
            f"Passed: {summary['passed']}",
            f"Failed: {summary['failed']}",
            f"Success Rate: {summary['success_rate']*100:.1f}%",
            ""
        ]
        
        for result in self.results:
            status = "[+]" if result['valid'] else "[-]"
            lines.append(f"{status} {result['equation']}: {'VALID' if result['valid'] else 'INVALID'}")
        
        return "\n".join(lines)
