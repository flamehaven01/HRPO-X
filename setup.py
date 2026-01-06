from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hrpo-x",
    version="1.0.1",
    author="CLI C01",
    author_email="cli@flamehaven.io",
    description="Hybrid Reasoning with Policy Optimization - Production Implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flamehaven01/HRPO-X",
    packages=["hrpox"],
    py_modules=["hrpo_core_v2_2"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-cov>=4.1.0",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hrpo-train=training.trainer:main",
            "hrpo-eval=training.evaluate:main",
        ],
    },
)
