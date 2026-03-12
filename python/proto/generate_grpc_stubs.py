import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROTO_DIR = WORKSPACE_ROOT / "proto"
PROTO_FILE = PROTO_DIR / "algsolver.proto"
PY_OUT_DIR = Path(__file__).resolve().parent
STUB_FILE = PY_OUT_DIR / "algsolver_pb2.py"
STUB_GRPC_FILE = PY_OUT_DIR / "algsolver_pb2_grpc.py"
PYRIGHT_HEADER = "# pyright: reportAttributeAccessIssue=false\n"


def _postprocess_generated_files() -> None:
    if STUB_FILE.exists():
        text = STUB_FILE.read_text(encoding="utf-8")
        if not text.startswith(PYRIGHT_HEADER):
            STUB_FILE.write_text(PYRIGHT_HEADER + text, encoding="utf-8")

    if STUB_GRPC_FILE.exists():
        text = STUB_GRPC_FILE.read_text(encoding="utf-8")
        text = text.replace(
            "import algsolver_pb2 as algsolver__pb2",
            "from . import algsolver_pb2 as algsolver__pb2",
            1,
        )
        if not text.startswith(PYRIGHT_HEADER):
            text = PYRIGHT_HEADER + text
        STUB_GRPC_FILE.write_text(text, encoding="utf-8")


def stubs_are_stale() -> bool:
    if not STUB_FILE.exists() or not STUB_GRPC_FILE.exists():
        return True
    proto_mtime = PROTO_FILE.stat().st_mtime
    return proto_mtime > min(STUB_FILE.stat().st_mtime, STUB_GRPC_FILE.stat().st_mtime)


def generate() -> int:
    if not PROTO_FILE.exists():
        print(f"Missing proto file: {PROTO_FILE}")
        return 1

    if not stubs_are_stale():
        _postprocess_generated_files()
        print("gRPC stubs are up-to-date.")
        return 0

    print("Generating gRPC stubs...")
    cmd = [
        "python",
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={PY_OUT_DIR}",
        f"--grpc_python_out={PY_OUT_DIR}",
        str(PROTO_FILE),
    ]
    completed = subprocess.run(cmd, check=False)
    if completed.returncode == 0:
        _postprocess_generated_files()
        print("Done.")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(generate())
