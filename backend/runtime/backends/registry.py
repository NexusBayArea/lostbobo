from .mfem_backend import MFEMBackend

BACKENDS = {
    "mfem.solve": MFEMBackend(),
}
