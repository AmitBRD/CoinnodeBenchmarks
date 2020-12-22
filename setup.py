import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="adapter-load-tester", # Replace with your own username
    version="0.0.1",
    author="Amit",
    author_email="amit@breadwallet.com",
    description="A small load tester configuration using locust",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
     install_requires = [
        "locust",
        "aiofile",
        "aiohttp"
        ] 

)