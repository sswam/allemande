from setuptools import setup, find_packages

# Read the contents of requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hello-example",
    version="1.0.0",
    author="Sam Watkins",
    author_email="sam@ucm.dev",
    description="A not-so-simple hello world example script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sswam/allemande/tree/main/python",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "hello-example=hello:main",
        ],
    },
    extras_require={
        'dev': ['pytest'],
    },
)

