"""
Siemply - Splunk Infrastructure Orchestration Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="siemply",
    version="1.0.0",
    author="Siemply Framework",
    author_email="support@siemply.dev",
    description="A lightweight, opinionated orchestration framework for managing Splunk deployments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/siemply/siemply",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Clustering",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "vault": ["hvac>=1.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "siemply=siemply.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "siemply": [
            "config/*.yml",
            "config/*.yaml",
            "plays/*.yml",
            "plays/*.yaml",
            "scripts/*.py",
        ],
    },
    zip_safe=False,
    keywords="splunk, orchestration, automation, infrastructure, deployment, universal-forwarder, enterprise",
    project_urls={
        "Bug Reports": "https://github.com/siemply/siemply/issues",
        "Source": "https://github.com/siemply/siemply",
        "Documentation": "https://docs.siemply.dev",
    },
)
