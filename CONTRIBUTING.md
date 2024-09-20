# Contributing to Django-drip-campaigns

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html), So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we use [Github Flow](https://guides.github.com/introduction/flow/index.html)). We actively welcome your pull requests:

1. Fork the repo and create your branch from `master`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/briandk/transcriptase-atom/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](); it's that easy!

## Write bug reports with detail, background, and sample code

[This is an example](http://stackoverflow.com/q/12488905/180626) of a bug report.
Here's [another example from Craig Hockenberry](http://www.openradar.me/11905408), an app developer whom I greatly respect.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can. [My stackoverflow question](http://stackoverflow.com/q/12488905/180626) includes sample code that _anyone_ with a base Project setup can run to reproduce what I was seeing
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People _love_ thorough bug reports. I'm not even kidding.

## For new feature proposals open a RFC

- Open an issue with the tag RFC
- Include the following sections in the issue description
  - ### What do you want and why?
  - ### How is this different from what you are currently doing?
  - ### Possible implementation

## How to develop locally and run the tests

We recommend you to use:

- [pyenv](https://github.com/pyenv/pyenv): To easily install and manage different versions of Python.
- [pipenv](https://pipenv.pypa.io/en/latest/): To create and manage Python virtual environments.

The Python version we recommend to develop with: The latest (currently 3.12) but avoiding (if possible) to use elements
that are exclusively from that version and don't work in previous versions. This is because we want to be compatible
with older versions of Python.

### Python versions we are currently testing (Sept, 2024)

- 3.8.19
- 3.9.19
- 3.10.14
- 3.11.9
- 3.12.4

### Step by step to run the tests

1. Install with pyenv the different versions of Python, so you can use the latest to develop, and the other ones to
   run the tests and check that the compatibility with older versions continues.
   - `pyenv install <python version>`
   - Run this for each version.
2. Go to the project folder in the terminal.
3. Set the versions of python to be locally available in the folder:
   - `pyenv local 3.8.19 3.9.19 3.10.14 3.11.9 3.12.4`
   - This will create a gitignored file called `.python-version` listing these versions.
4. Create the virtual environment using the latest version:
   - `pipenv install --python 3.12.4`
   - This will create and install in it the base and dev requirements. You can check this on the Pipfile.
5. Enter the virtual environment:
   - `pipenv shell`
6. Run the tests:
   - `pytest .`
   - They should pass without errors.
7. Now run the tox command that will run the tests using different versions of python:
   - `tox`
   - This will run the tests with different Python versions using the `tox.ini` file.
   - It will install the base requirements from the `install_requires` list in the `setup.py` file, and the dev requirements
     from the `test-requirements.txt` file that has the list of the needed dev libraries.
   - You will see the tests execution for each version of Python.
   - You can run `tox -v` to see more details.

## Use a Consistent Coding Style

I'm again borrowing these from [Rootstrap Tech Guides](https://github.com/rootstrap/tech-guides/tree/master/python)

- 4 spaces for indentation rather than tabs
- You can try running `flake8 .` for style unification
- In this project we decided to use the `format()` function for string formatting. We prefer to use `f strings`, but since we want to keep support for Python 3.5, we can't use that. Example:

```python
x = 3
print('Number in var x is: {x}'.format(x=x))
```

## Update the version

Before creating the pull request, please update the version in `drip/__inti__.py` following the next rules:

- If you are doing a fix, then bump the third digit.
- If you are doing a non breaking change, then bump the second digit.
- If you are doing a breaking change, then bump the first digit.

We have Github Actions configured to automatically release the changes in master branch.

If you are doing changes in the docs, you have to:

- Keep the version unchanged.
- Make sure the branch name starts with `docs/`. For example: `docs/update-drip-class-description`.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## References

This document was adapted from the open-source contribution guidelines for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)
