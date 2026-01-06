"""
HRPO-X v1.0.1 - Configuration Schema
====================================
Pydantic-based validated configuration schema
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Optional


class ValidationConfig(BaseModel):
    """Validation settings"""
    enabled: bool = Field(default=True, description="Enable validation")
    level: str = Field(default="development", description="Validation level: development|testing|production")
    fail_on_warning: bool = Field(default=True, description="Fail on warnings in dev mode")
    collect_metrics: bool = Field(default=True, description="Collect validation metrics")
    
    # Individual check toggles
    equation_integrity: bool = Field(default=True, description="Validate Equations 3/4/6")
    numerical_stability: bool = Field(default=True, description="Check NaN/Inf")
    patch_behavior: bool = Field(default=True, description="Validate patches")
    training_health: bool = Field(default=True, description="Training health checks")
    
    @validator('level')
    def validate_level(cls, v):
        allowed = ['development', 'testing', 'production']
        if v not in allowed:
            raise ValueError(f'level must be one of {allowed}')
        return v


class HRPOConfigSchema(BaseModel):
    """Validated HRPO configuration schema"""
    
    # Core hyperparameters
    beta: float = Field(default=0.005, ge=0.0, le=0.1, description="KL coefficient")
    learning_rate_base: float = Field(default=5e-6, gt=0.0, description="Base learning rate")
    
    # Gating parameters  
    tau: float = Field(default=0.5, gt=0.0, description="Temperature parameter")
    c: float = Field(default=8.0, gt=0.0, description="Scaling constant")
    
    # r_min range
    r_min_range: tuple = Field(default=(0.90, 0.99), description="Min/max for r_min")
    
    # Validation config
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    
    @validator('r_min_range')
    def validate_rmin_range(cls, v):
        if len(v) != 2:
            raise ValueError('r_min_range must be (min, max)')
        if v[0] >= v[1]:
            raise ValueError('r_min_range[0] must be < r_min_range[1]')
        if not (0.0 < v[0] < 1.0 and 0.0 < v[1] < 1.0):
            raise ValueError('r_min_range values must be in (0, 1)')
        return v
    
    class Config:
        validate_assignment = True
