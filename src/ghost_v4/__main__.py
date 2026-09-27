from ._bootstrap import ensure_dependencies

ensure_dependencies()

from .cli import main  # noqa: E402

main()
