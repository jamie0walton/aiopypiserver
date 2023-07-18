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

# Requires

Started with python 3.11 on Windows 10, immediately wanted to run on Debian with python 3.9.

Building required a whole bunch of stuff, some of which will not be required. Perhaps none are
needed to run???

```
 pip3 install --upgrade pep517
 pip3 install --upgrade wheel
 pip3 install --upgrade build
 pip3 install --upgrade setuptools
 pip3 install --upgrade importlib
 pip3 install --upgrade requests
 ``

Thanks to [bug report](https://github.com/robhagemans/monobit/issues/22) for the fix for
importlib_resources. The ```__init__.py``` inclusion in assets did the trick.
