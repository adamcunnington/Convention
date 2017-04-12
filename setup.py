import setuptools

setuptools.setup(
    name="Convention",
    version="0.1",
    author="Adam Cunnington",
    author_email="ac@adamcunnington.info",
    packages=setuptools.find_packages(),
    install_requires=["flask", "flask-sqlalchemy", "flask-oauthlib"]
)
