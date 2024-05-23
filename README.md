# NREL Engage: A [Calliope](https://github.com/calliope-project/calliope) Web Environment for Collaborative Energy Systems Modeling and Planning

Engage is a free, open-access energy system planning tool that allows multiple users/stakeholders to develop and collaborate on capacity expansion models. The tool, developed at the National Renewable Energy Laboratory (NREL), provides a collaborative and easy-to-use interface built on Calliope, a multi-scale energy systems modeling framework.

- Visit the NREL hosted webtool at https://engage.nrel.gov/


## Requirements
- Docker (https://www.docker.com/get-started)
- Docker Compose (e.g. ```brew install docker-compose```)


## Setup Public Stream

``` bash
$ git remote add public https://github.com/NREL/engage.git
$ git remote -v # check
$ git remote set-url --push public DISABLE
```
IMPORTANT! Please never `push` to the `public` stream.

## Fetch Public Updates

For dev branch
```bash
$ git checkout dev
$ git fetch public
$ git merge public/dev
```

For master branch
```bash
$ git checkout master
$ git fetch public
$ git merge public/master
```

## NREL Deploy

Jenkins - https://jenkins.nrelcloud.org/login?from=%2F

* `dev` branch deploy on dev environment.
* `master` branch deploy on production environment. 


## Documentation
https://nrel.github.io/engage


## License
BSD 3-Clause License
https://github.com/NREL/engage/blob/master/LICENSE