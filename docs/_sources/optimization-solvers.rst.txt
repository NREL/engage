Optimization Solvers
====================

GLPK
----
Engage uses a free and open-source solver `GLPK <https://www.gnu.org/software/glpk/>`_
for development purpose, and it is already built into the docker image.

GLPK supports the GNU MathProg modeling language - subset of the AMPL language, and include
a variety of components, for detailed information, please refer to https://www.gnu.org/software/glpk/.

However, it takes too much time and memory for solving large Calliope models.

SCIP
----
`SCIP <https://scip.zib.de/>`_ is currently one of the fastest non-commercial solvers for mixed integer programming (MIP)
and mixed integer nonlinear programming (MINLP). It is also a framework for constraint integer
programming and branch-cut-and-price. It allows for total control of the solution process and
the access of detailed information down to the guts of the solver.

However we didn't provide in docker environment for development purpose, if you need, here are the steps for installing SCIP solver,

.. code-block:: bash

    $ cd ~/scipoptsuite-5.0.0/ && make
    $ cd ~/scipoptsuite-5.0.0/scip/interfaces/ampl/ && ./get.ASL -y
    $ cd ~/scipoptsuite-5.0.0/scip/interfaces/ampl/solvers/ && sh configurehere && make
    $ cd ~/scipoptsuite-5.0.0/scip/interfaces/ampl/ && make
    $ cp ~/scipoptsuite-5.0.0/scip/interfaces/ampl/bin/scipampl /usr/local/bin/


HiGHS
------

In the deployed Engage application at NREL, it uses commercial `FICO XPRESS <https://www.fico.com/en/products/fico-xpress-optimization>`_ 
to solve Calliope models with fast speed and large memory in compute node.

HiGHS
------

NREL Engage deployment also integrates the commercial solver `FICO XPRESS <https://www.fico.com/en/products/fico-xpress-optimization>`_
to solve Calliope models with high performance and large compute resources.

More Choice
-----------
In behind, Calliope interfaces to `Pyomo <http://www.pyomo.org/>`_  - a Python-based, open-source optimization modeling language with
a diverse set of optimization capabilities. With the `API interface <https://calliope.readthedocs.io/en/v0.6.8/api/api.html#api-backend-interface>`_
provided by Calliope, you can specify the customized solver options.

For more solver choice, please refer to `specifying-custom-solver-options
<https://calliope.readthedocs.io/en/stable/user/advanced_features.html#specifying-custom-solver-options>`_

Refer to `influence-of-solver-choice-on-speed
<https://calliope.readthedocs.io/en/stable/user/troubleshooting.html#influence-of-solver-choice-on-speed>`_
for more information about problem solving speed with different solvers.
