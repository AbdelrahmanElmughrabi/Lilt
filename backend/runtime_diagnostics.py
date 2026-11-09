"""Request ONNX's supported event opt-out for the module selected in this process.

The Python API is available only after import. Its return does not attest native
event suppression, ETW attachment behavior or the absence of platform traffic.
"""


DIAGNOSTICS_FAILURE_MESSAGE = (
    "The voice runtime's diagnostic settings could not be applied. "
    "Restart Violilt; if this continues, repair the installation."
)


class RuntimeDiagnosticsError(RuntimeError):
    """The selected runtime could not apply the required diagnostic request."""


def load_onnx_runtime():
    import onnxruntime as ort

    # Repeat at each entry boundary; a previous request is not a durable native
    # state readback and must not authorize a different module or worker.
    try:
        ort.disable_telemetry_events()
    except Exception:
        raise RuntimeDiagnosticsError(DIAGNOSTICS_FAILURE_MESSAGE) from None
    return ort
