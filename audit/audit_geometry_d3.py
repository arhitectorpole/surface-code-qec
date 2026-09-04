"""Run the frozen d=3 geometry audit for decoder_lib_v2."""

from src.decoder_lib_v2 import audit_geometry, build_decoding_graph


def main() -> int:
    report = audit_geometry(build_decoding_graph(3))
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
