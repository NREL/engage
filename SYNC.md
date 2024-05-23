# Private Sync Public Git Workflow

## Setup Two Repositories

### 1. Create Two Repos

* Create a `Public` repo named `engage` on `https://github.com/NREL`.
* Create a `Private` repo named `engage-private` on `https://github.nrel.gov/`.

### 2. Clone `--bare` from Public Repo

```bash
$ git clone --bare https://github.com/NREL/engage.git
```
The bare cloned repo at disk ends with `.git` suffix.

### 3. Push `--mirror` to Private Repo

```bash
$ cd engage.git
$ git push --mirror https://github.nrel.gov/rspencer/engage-private.git
$ cd ..
$ rm -rf engage.git
```
The bare repo of `engage.git` does not need anymore, and is deleted after push.

### 4. Add `Public` Stream and Disable `push`

```bash
$ git clone https://github.nrel.gov/rspencer/engage-private.git
$ cd engage-private
$ git remote add public https://github.com/NREL/engage.git
$ git remote -v # check
$ git remote set-url --push public DISABLE
```

## Define Development Workflow

### 1. Development in Public Repo

```bash
$ git clone https://github.com/NREL/engage.git
```
Develop in `engage` repo, then add, commit, and push updates to `engage` public repo.

### 2. Sync Public Updates to Private

```bash
$ cd engage-private
$ git fetch public
$ git merge public/branch-name
```

### 3.  (Optional) Development in Private Repo

The private `engage-private` repo is used for deployment purpose at NREL only, please do not develop engage features in this repo, that should happen in public `engage` repo.

The development in private `engage-private` repo should be deployment related, like docker container, bash scripts, deployment required settings, etc.
