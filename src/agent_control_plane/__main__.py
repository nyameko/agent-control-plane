"""Development entry point."""

import uvicorn


def main() -> None:
    uvicorn.run("agent_control_plane.api:app", host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
