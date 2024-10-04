Contributing to Engage
======================

Issue Tracking
--------------
We welcome bug reports, feature requests and pull requests through Engage's `Github issue tracker <https://github.com/NREL/Engage/issues>`_.

The issues submitted via the issue tracker corresponds to a specific action with a well-defined completion state:
Bugfix, New Feature, Documentation Update, Code Clean-up. After an issue ticket is opened, a member of Engage team will give it an initial classification,
make a valiation, response, close and/or assign it to a milestone.


Pull Requests
-------------
We are welcome to any contribution from outside of NREL, the contributions can make this web tool better.
Please follow the following steps to contribute to this project.

1. Fork this repository to your account.
2. Checkout your own feature branch.
3. Develop features in the docker environment.
4. Test your feature branch by using Django test framework.
5. Update documentation if necessary.
6. Create a pull request to our ``dev`` branch.
7. NREL reviews, tests and merges the pull request.

.. Note::

    Please note that this may generate cost under your AWS account if there were ``AWS SES``
    operations during the development process. This feature is optional to setup.

Thanks for Contribution!


Update Documenttation
---------------------
To update the Sphinx documentation here, use command below:

.. code-block:: bash

    $ cd docs
    $ make docs
    $ git push origin branch-name

The updatetd documentation will display after `branch-name` merged into master.
