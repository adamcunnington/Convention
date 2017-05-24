import setuptools

setuptools.setup(
    name="Convention",
    version="0.1",
    author="Adam Cunnington",
    author_email="ac@adamcunnington.info",
    package_data={"": ("../convention.db", "*.env", "instance/*", "static/styles/*", "templates/*", "*/templates/*", "*/static/styles/*")},
    packages=setuptools.find_packages(),
    install_requires=[
        "flask",
        "flask-httpauth",
        "flask-login",
        "flask-sqlalchemy",
        "flask-oauthlib",
        "flask-wtf",
        "python-dotenv",
        "wrapt",
        "wtforms"
    ]
)
