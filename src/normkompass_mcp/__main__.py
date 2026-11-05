"""Entry point: run the server over stdio."""

from .server import build_server


def main() -> None:
    build_server().run("stdio")


if __name__ == "__main__":
    main()
