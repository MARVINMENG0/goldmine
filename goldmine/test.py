#! /usr/bin/env python

from __future__ import absolute_import, division, print_function

import argparse
import logging
from os import sys, path
import numpy as np

base_dir = path.abspath(path.join(path.dirname(__file__), '..'))

try:
    from goldmine.various.look_up import create_inference
    from goldmine.various.utils import general_init
except ImportError:
    if base_dir in sys.path:
        raise
    sys.path.append(base_dir)
    print(sys.path)
    from goldmine.various.look_up import create_inference
    from goldmine.various.utils import general_init


def test(simulator_name,
         inference_name,
         alpha=1.,
         training_sample_size=None):
    """ Main training function """

    # Folders
    sample_folder = base_dir + '/goldmine/data/samples/' + simulator_name
    model_folder = base_dir + '/goldmine/data/models/' + simulator_name + '/' + inference_name
    result_folder = base_dir + '/goldmine/data/results/' + simulator_name + '/' + inference_name

    # Filenames
    sample_filename = simulator_name + '_test'
    model_filename = simulator_name + '_' + inference_name
    if training_sample_size is not None:
        model_filename += '_trainingsamplesize_' + str(training_sample_size)

    # Load test data
    thetas = np.load(sample_folder + '/' + sample_filename + '_theta0.npy')
    xs = np.load(sample_folder + '/' + sample_filename + '_x.npy')

    n_parameters = thetas.shape[1]
    n_observables = xs.shape[1]

    inference = create_inference(
        inference_name,
        n_parameters=n_parameters,
        n_observables=n_observables,
        alpha=alpha
    )

    # Load model
    inference.load(model_folder + '/' + model_filename + '.pt')

    # Evaluate on test sample
    log_p_hat = inference.predict_density(xs, thetas, log=True)

    # Save results
    np.save(result_folder + '/' + model_filename + '_log_p_hat.pt', log_p_hat)


def main():
    """ Starts training """

    # Set up logging and numpy
    general_init()

    # Parse arguments
    parser = argparse.ArgumentParser(description='Likelihood-free inference experiments with gold from the simulator')

    parser.add_argument('simulator', help='Simulator: "galton" or "epidemiology"')
    parser.add_argument('inference', help='Inference method: "maf" or "scandal"')
    parser.add_argument('--alpha', type=float, default=1.,
                        help='alpha parameter for SCANDAL')
    parser.add_argument('--trainingsamplesize', type=int, default=None,
                        help='Number of (training + validation) samples considered')

    args = parser.parse_args()

    logging.info('Start-up options:')
    logging.info('  Simulator:            %s', args.simulator)
    logging.info('  Inference method:     %s', args.inference)
    logging.info('  alpha:                %s', args.alpha)
    logging.info('  Training sample size: %s',
                 'maximal' if args.trainingsamplesize is None else args.trainingsamplesize)

    # Start simulation
    test(
        args.simulator,
        args.inference,
        alpha=args.alpha,
        training_sample_size=args.trainingsamplesize
    )

    logging.info("That's all for now, have a nice day!")


if __name__ == '__main__':
    main()
