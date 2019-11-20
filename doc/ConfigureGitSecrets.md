# Configure git-secrets
git-secrets appears to be intended primarily to prevent AWS keys from being 
committed, but we can use its regex capability to prevent 
specific code from being committed.

### Acquire git-secrets

```commandline
cd \some\git\path`

git clone https://github.com/awslabs/git-secrets.git
```

* Copy git-secrets to a system path directory, e.g. `C:\Python36\Scripts` 

* Test
```commandline
git secrets

C:\Will.Smith\git\git-secrets>git secrets
usage: git secrets --scan [-r|--recursive] [--cached] [--no-index] [--untracked] [<files>...]
   ... etc
```

* Install git hooks on selected project
```commandline
cd C:\Will.Smith\git\pyqt5-framdata\pyqt5-framdata
C:\Will.Smith\git\pyqt5-framdata>git secrets --install
√ Installed commit-msg hook to .git/hooks/commit-msg
√ Installed pre-commit hook to .git/hooks/pre-commit
√ Installed prepare-commit-msg hook to .git/hooks/prepare-commit-msg

```
* Install secrets to search (via file)
  * Note that windows and git grep are very finicky:
   Don't use spaces or escaped quotes, instead
    use \s for whitespace as below, ['"] for quotes
```python
#Example:
#Search for following line:
self.test_unhashed_pw = 'something not empty'
self.test_unhashed_pw = '' # but this is OK
```
```commandline
git secrets --add self\.test_unhashed_pw\s*=\s*['"].+['"]"
git secrets --scan
test/test_observer_soap.py:19:        self.test_unhashed_pw = 'badness'  # DO NOT COMMIT PW
[ERROR] Matched one or more prohibited patterns
```

* To clear git secrets from repo
```commandline
git config --unset-all secrets.patterns
git config --unset-all secrets.providers
```