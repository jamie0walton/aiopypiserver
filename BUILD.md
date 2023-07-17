# Intro

This is a record of most of the steps I've taken creating this repository.

Start with creating a public repo on Github with GPL v3.

```
git clone https://github.com/jamie0walton/aiopypiserver.git
```

I want to be able to upload, start with pypiserver locally
```
# open folder in VS Code
# terminal opens in folder
pip install build twine
```

Create initial framework of config and folders, enough to run test.

```
# Ctrl Shft P - Python: Configure Tests, select pytest
python -m build
pip install --editable .
python -m twine upload --repository pypi dist/*
```

This is the minimal first setup. Nothing useful other than the framework at this point.

# Dev cycle

Select flake8 and 

Build cycle is something like.
```
python -m build
pip install --editable .
python -m aiopypiserver
aiopypiserver
git status
# branch should not be main
git add .
git commit -m "<comment>"
git push
# merge on github, have a look at how to flatten branches before merge.
aiopypiserver
# in another terminal, but in the project dir
python -m twine upload --repository-url http://localhost:8080/ dist/*
```
