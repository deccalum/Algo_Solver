from pathlib import Path
import subprocess
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    proto_dir = root.parent / "proto"
    proto_file = proto_dir / "algsolver.proto"
    py_out = root / "algsolver_pb2.py"
    py_grpc_out = root / "algsolver_pb2_grpc.py"

    if not proto_file.exists():
        print(f"Missing proto file: {proto_file}")
        return 1

    if py_out.exists():
        py_out.unlink()
    if py_grpc_out.exists():
        py_grpc_out.unlink()

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={root}",
        f"--grpc_python_out={root}",
        str(proto_file),
    ]

    completed = subprocess.run(cmd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
