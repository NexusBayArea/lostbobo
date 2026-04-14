import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode not in {"ci", "worker", "dev", "test"}:
        raise ValueError(f"Invalid mode: {args.mode}")

    if args.dry_run:
        print(f"[DRY RUN] mode={args.mode}")
        return

    if args.mode == "ci":
        from app.runtime.dag import run_ci_dag

        run_ci_dag()

    elif args.mode == "worker":
        from app.runtime.dag import run_worker_dag

        run_worker_dag()

    elif args.mode == "dev":
        from app.runtime.dag import run_dev_dag

        run_dev_dag()

    elif args.mode == "test":
        from app.runtime.dag import DAG
        from app.runtime.executor import Executor
        from worker.tasks import task_a, task_b

        dag = DAG()
        dag.add("task_a", task_a)
        dag.add("task_b", task_b, deps=["task_a"])

        executor = Executor(dag)
        result = executor.run()

        print("\n=== DAG TEST RESULT ===")
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
