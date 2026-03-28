"""
Setup script for Seedance SDK
"""
from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="seedance-sdk",
    version="1.0.0",
    author="Seedance Team",
    author_email="support@vibegen.art",
    description="Python SDK for Seedance AI Video Generation API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tc1989tc/seedance-api",
    project_urls={
        "Bug Tracker": "https://github.com/tc1989tc/seedance-api/issues",
        "Documentation": "https://vibegen.art/docs",
        "Source Code": "https://github.com/tc1989tc/seedance-api",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "types-requests",
        ],
        "webhook": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai video generation api seedance",
)
