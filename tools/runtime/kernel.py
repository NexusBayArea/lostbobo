from tools.runtime.contract import CONTRACT


def validate_contract():
    # ONLY structural check (no logic ownership)
    required_attrs = ["root", "entrypoints", "allowed_roots", "forbidden_prefixes"]

    for attr in required_attrs:
        if not hasattr(CONTRACT, attr):
            raise RuntimeError(f"Contract missing: {attr}")


def main():
    print("[KERNEL] boot sequence start")

    validate_contract()

    print("[KERNEL] execution layer active")
    print("[KERNEL] boot sequence complete")


if __name__ == "__main__":
    main()
