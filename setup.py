import setuptools

setuptools.setup(
    name="Convention",
    version="0.1",
    author="Adam Cunnington",
    author_email="ac@adamcunnington.info",
    package_data={"": ("*.env", "templates/*", "static/*")},
    packages=setuptools.find_packages(),
    install_requires=[
        "flask",
        "flask_httpauth",
        "flask-login",
        "flask-sqlalchemy",
        "flask-oauthlib",
        "flask-wtf",
        "python-dotenv",
        "wrapt",
        "wtforms"
    ]
)
