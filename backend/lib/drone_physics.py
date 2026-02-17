import sys
import os
import importlib.util
import numpy as np

# This module acts as a bridge. 
# It tries to load the PAVPhysics class from the user-code repository.
# If not found, it falls back to a local definition (or raises an error).

# Path is relative to backend root or defined by env
USER_CODE_ROOT = os.environ.get("USER_CODE_PATH", "../beam-user-code") 
PHYSICS_LIB_REL_PATH = "libs/physics/pav_physics.py"
FULL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "beam-user-code", PHYSICS_LIB_REL_PATH)

# Check if environment variable overrides
if os.environ.get("USER_CODE_PATH"):
    FULL_PATH = os.path.join(os.environ["USER_CODE_PATH"], PHYSICS_LIB_REL_PATH)

PAVPhysics = None
RHO_STD = 0.002378
MPH_TO_FTS = 1.46667

# 1. Try to load from User Code Repo
if os.path.exists(FULL_PATH):
    try:
        spec = importlib.util.spec_from_file_location("pav_physics", FULL_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules["user_pav_physics"] = module
        spec.loader.exec_module(module)
        
        # Capture the class
        if hasattr(module, "PAVPhysics"):
            PAVPhysics = module.PAVPhysics
        
        # Capture constants if present
        if hasattr(module, "RHO_STD"):
            RHO_STD = module.RHO_STD
        if hasattr(module, "MPH_TO_FTS"):
            MPH_TO_FTS = module.MPH_TO_FTS
            
        print(f"[System] Successfully loaded PAVPhysics from user repo: {FULL_PATH}")
    except Exception as e:
        print(f"[System] Warning: Failed to load external physics lib from {FULL_PATH}: {e}")

# 2. Fallback Definition (if user repo not present or broken)
if PAVPhysics is None:
    print("[System] Using fallback PAVPhysics implementation.")
    
    class PAVPhysics:
        """Fallback implementation if user-code is missing."""
        @staticmethod
        def get_air_density(altitude_ft=0, temp_f=59, sigma=1.0):
            return RHO_STD * sigma

        @staticmethod
        def calc_lift_coefficient(W, rho, V_ft_s, S):
            if V_ft_s < 1: return 0.0
            return (2 * W) / (rho * (V_ft_s**2) * S)

        @staticmethod
        def calc_drag(W, rho, V_ft_s, S, AR, e, CDw, Aw):
            if V_ft_s < 10: return float('inf')
            CL = PAVPhysics.calc_lift_coefficient(W, rho, V_ft_s, S)
            if CL == 0: return float('inf')
            try:
                # Drag = Induced + Profile
                # Drag = Lift * (CL / (pi * AR * e) + (CDw * Aw) / (CL * S))
                induced = CL / (np.pi * AR * e)
                profile = (CDw * Aw) / (CL * S)
                return W * (induced + profile)
            except:
                return float('inf')

        @staticmethod
        def calc_hover_power_kw(W, Ae, eta_vtol=0.7, sigma=0.93):
            rho = sigma * RHO_STD
            try:
                p_ideal_ft_lbs = (W ** 1.5) / np.sqrt(2 * rho * Ae)
                return (p_ideal_ft_lbs / 550.0) / eta_vtol * 0.7457
            except:
                return float('inf')
                
        @staticmethod
        def calc_cruise_power_kw(drag_lbs, V_ft_s, eta_cruise=0.8):
            if eta_cruise <= 0: return float('inf')
            power_hp = (drag_lbs * V_ft_s) / (550 * eta_cruise)
            return power_hp * 0.7457
        
        @staticmethod
        def calc_dynamic_pressure(rho, V):
            return 0.5 * rho * (V**2)
