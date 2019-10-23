import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True

source_files = ("ddtrace_asgi", "tests", "setup.py", "noxfile.py")


@nox.session
def lint(session: nox.sessions.Session) -> None:
    session.install("autoflake", "black", "flake8", "isort", "seed-isort-config")

    session.run("autoflake", "--in-place", "--recursive", *source_files)
    session.run("seed-isort-config", "--application-directories=ddtrace_asgi")
    session.run(
        "isort", "--project=ddtrace_asgi", "--recursive", "--apply", *source_files
    )
    session.run("black", "--target-version=py36", *source_files)

    check(session)


@nox.session
def check(session: nox.sessions.Session) -> None:
    session.install(
        "black", "flake8", "flake8-bugbear", "flake8-comprehensions", "isort", "mypy"
    )

    session.run("black", "--check", "--diff", "--target-version=py36", *source_files)
    session.run("flake8", *source_files)
    session.run("mypy", *source_files)
    session.run(
        "isort",
        "--check",
        "--diff",
        "--project=ddtrace_asgi",
        "--recursive",
        *source_files,
    )


@nox.session(python=["3.6", "3.7", "3.8"])
def test(session: nox.sessions.Session) -> None:
    session.install("-r", "requirements.txt")
    session.run("python", "-m", "pytest", *session.posargs)
