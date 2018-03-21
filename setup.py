import setuptools

setuptools.setup(
    name="dft_bare_susceptibility",
    version="0.1",
    python_requires=">=3.5",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy>=1.14.1",
    ],
)
