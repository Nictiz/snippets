# UpVersionNumbers

Increase the patch level version number by 1 for all profiles (or other resources containing a `<version value="x.y.z"/>` tag) that have been changed in the current git branch, as compared to the base branch.

Usage:

* Navigate to the git folder containing the changed files.
* Checkout the branch with the changed files.
* Run the script
    python3 upversionnumbers.py [base_branch]

`base_branch` is the name of the base branch to compare this branch to.