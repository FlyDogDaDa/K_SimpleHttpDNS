from setuptools import setup

setup(
    name="k_simple_http_dns",
    version="0.1.0",
    description="The local network is scattered with many small ai services, and this package helps manage these hosts and ports.",
    author="HSU, MING-SHUN",
    author_email="54river0522@gmail.com",
    packages=["k_simple_http_dns"],
    install_requires=["pydantic", "requests", "fastapi", "uvicorn"],
)
