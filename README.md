# NREL Engage: A [Calliope](https://github.com/calliope-project/calliope) Web Environment for Collaborative Energy Systems Modeling and Planning

Engage is a free, open-access energy system planning tool that allows multiple users/stakeholders to develop and collaborate on capacity expansion models. The tool, developed at the National Renewable Energy Laboratory (NREL), provides a collaborative and easy-to-use interface built on Calliope, a multi-scale energy systems modeling framework.

- Visit the NREL hosted webtool at https://engage.nrel.gov/


## Requirements
- Docker (https://www.docker.com/get-started)
- Docker Compose (e.g. ```brew install docker-compose```)


## Development

Please refer to the documentation to setup development environment,

https://nrel.github.io/engage

and the developer guide to contribute to Enage project.

## License
BSD 3-Clause License
https://github.com/NREL/engage/blob/master/LICENSE

## Documentation
In /engage/docs:
Update user documentation:
- make -f Makefile2 docs

Update developer documentation:
- make -f Makefile docs

Ignore the warning about the static directory. To get a preview of the documentation copy the file path and past it into the browser. Once the documentation is ready merge it into the gh-pages branch. To change the settings for sphinx update the conf.py file. To update the navbar layout of the page look at the index.rst file.