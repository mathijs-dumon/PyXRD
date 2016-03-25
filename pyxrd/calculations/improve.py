# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Copyright (c) 2013, Mathijs Dumon
# All rights reserved.
# Complete license can be found in the LICENSE file.

try:
    from cStringIO import StringIO #@UnusedImport
except:
    from StringIO import StringIO #@Reimport

from scipy.optimize import fmin_l_bfgs_b

from .exceptions import wrap_exceptions

def setup_project(projectf):
    from pyxrd.file_parsers.json_parser import JSONParser
    from pyxrd.project.models import Project
    type(Project).object_pool.clear()

    f = StringIO(projectf)
    project = JSONParser.parse(f)
    f.close()

    return project

@wrap_exceptions
def run_refinement(projectf, mixture_index, options):
    """
        Runs a refinement setup for 
            - projectf: project data
            - mixture_index: what mixture in the project to use
            - options: refinement options
    """
    if projectf is not None:
        from pyxrd.data import settings
        settings.initialize()

        from pyxrd.generic import pool
        pool.get_pool()

        # Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf

        import gc
        gc.collect()

        mixture = project.mixtures[mixture_index]
        mixture.refiner.update_refinement_treestore()
        mixture.refiner.setup_context(store=False) # we already have a dumped project
        context = mixture.refiner.context
        context.options = options

        mixture.refiner.refine()

        return list(context.best_solution), context.best_residual, (context.record_header, context.records) #@UndefinedVariable

@wrap_exceptions
def improve_solution(projectf, mixture_index, solution, residual, l_bfgs_b_kwargs={}):
    if projectf is not None:
        from pyxrd.data import settings
        settings.initialize()

        # Retrieve project and mixture:
        project = setup_project(projectf)
        del projectf

        mixture = project.mixtures[mixture_index]

        with mixture.data_changed.ignore():

            # Setup context again:
            mixture.update_refinement_treestore()
            mixture.refiner.setup_context(store=False) # we already have a dumped project
            context = mixture.refiner.context

            # Refine solution
            vals = fmin_l_bfgs_b(
                context.get_residual_for_solution,
                solution,
                approx_grad=True,
                bounds=context.ranges,
                **l_bfgs_b_kwargs
            )
            new_solution, new_residual = tuple(vals[0:2])

        # Return result
        return new_solution, new_residual
    else:
        return solution, residual
