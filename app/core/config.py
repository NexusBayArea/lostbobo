from app.core.boot.context import boot_context


def get_settings():
    if not boot_context.initialized:
        # Fallback for scripts that don't use the DAG yet
        from app.core.boot.engine import run_boot_dag
        run_boot_dag()

    return boot_context.settings
