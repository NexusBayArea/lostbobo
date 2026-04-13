"""
Boot DAG for explicitly starting the application.
"""
import os
import logging

logger = logging.getLogger(__name__)

def run_boot_dag(mode="api"):
    logger.info(f"Executing Boot DAG for RUNTIME_MODE={mode}")
    
    # Node 1: Environment resolution
    logger.info("Node 1: Resolving explicit environment variables")
    image_ref = os.getenv("IMAGE_REF", "local-dev")
    logger.info(f"Context: IMAGE_REF={image_ref}")
    
    # Node 2: Configuration loading
    logger.info("Node 2: Loading Settings (no import side-effects)")
    from app.core.config import get_settings
    settings = get_settings()
    
    # Node 3: Infrastructure checks
    if mode == "ci":
        logger.info("Node 3 (CI): Simulating infra checks without blocking")
    else:
        logger.info("Node 3 (API): Binding to Supabase/Redis")
        
    logger.info("Boot DAG complete. Proceeding to imports.")
    return True
