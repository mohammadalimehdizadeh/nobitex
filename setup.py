import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nobitex", # Replace with your own username
    version="0.0.1",
    author="MA. Mehdizadeh",
    author_email="mohammadali.mehdizadeh@yahoo.com",
    description="nobitex api package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mohammadalimehdizadeh/nobitex",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: General Public License v3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)