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

Still no idea about how to set this up for aiopypiserver to eventually be runnable. TODO.
