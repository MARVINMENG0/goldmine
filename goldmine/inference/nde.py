import numpy as np
import logging
import torch
from torch import tensor

from goldmine.inference.base import Inference
from goldmine.ml.models.maf import ConditionalMaskedAutoregressiveFlow
from goldmine.ml.trainer import train
from goldmine.ml.losses import negative_log_likelihood


class MAFInference(Inference):
    """ Neural conditional density estimation with masked autoregressive flows. """

    def __init__(self, **params):
        super().__init__()

        filename = params.get('filename', None)

        if filename is None:
            # Parameters for new MAF
            n_parameters = params['n_parameters']
            n_observables = params['n_observables']
            n_mades = params.get('n_mades', 2)
            n_made_hidden_layers = params.get('n_made_hidden_layers', 2)
            n_made_units_per_layer = params.get('n_made_units_per_layer', 20)
            activation = params.get('activation', 'relu')
            batch_norm = params.get('batch_norm', False)

            logging.info('Initialized NDE (MAF) with the following settings:')
            logging.info('  Parameters:    %s', n_parameters)
            logging.info('  Observables:   %s', n_observables)
            logging.info('  MADEs:         %s', n_mades)
            logging.info('  Hidden layers: %s', n_made_hidden_layers)
            logging.info('  Units:         %s', n_made_units_per_layer)
            logging.info('  Activation:    %s', activation)
            logging.info('  Batch norm:    %s', batch_norm)

            # MAF
            self.maf = ConditionalMaskedAutoregressiveFlow(
                n_conditionals=n_parameters,
                n_inputs=n_observables,
                n_hiddens=tuple([n_made_units_per_layer] * n_made_hidden_layers),
                n_mades=n_mades,
                activation=activation,
                batch_norm=batch_norm,
                input_order='sequential',
                mode='sequential',
                alpha=0.1
            )

        else:
            self.maf = torch.load(filename + '.pt')

            # Have everything on CPU (unless training)
            device = torch.device("cpu")
            self.maf = self.maf.to(device)

            logging.info('Loaded NDE (MAF) from file:')
            logging.info('  Filename:      %s', filename)
            logging.info('  Parameters:    %s', self.maf.n_conditionals)
            logging.info('  Observables:   %s', self.maf.n_inputs)
            logging.info('  MADEs:         %s', self.maf.n_mades)
            logging.info('  Hidden layers: %s', self.maf.n_hiddens)
            logging.info('  Activation:    %s', self.maf.activation)
            logging.info('  Batch norm:    %s', self.maf.batch_norm)

    def requires_class_label(self):
        return False

    def requires_joint_ratio(self):
        return False

    def requires_joint_score(self):
        return False

    def fit(self,
            theta=None,
            x=None,
            y=None,
            r_xz=None,
            t_xz=None,
            batch_size=64,
            initial_learning_rate=0.001,
            final_learning_rate=0.0001,
            n_epochs=50,
            early_stopping=True,
            alpha=None,
            learning_curve_folder=None,
            learning_curve_filename=None,
            **params):
        """ Trains MAF """

        logging.info('Training NDE (MAF) with settings:')
        logging.info('  theta given:    %s', theta is not None)
        logging.info('  x given:        %s', x is not None)
        logging.info('  y given:        %s', y is not None)
        logging.info('  r_xz given:     %s', r_xz is not None)
        logging.info('  t_xz given:     %s', t_xz is not None)
        logging.info('  Samples:        %s', x.shape[0])
        logging.info('  Parameters:     %s', theta.shape[1])
        logging.info('  Obserables:     %s', x.shape[1])
        logging.info('  Batch size:     %s', batch_size)
        logging.info('  Learning rate:  %s initially, decaying to %s', initial_learning_rate, final_learning_rate)
        logging.info('  Early stopping: %s', early_stopping)
        logging.info('  Epochs:         %s', n_epochs)

        train(
            model=self.maf,
            loss_functions=[negative_log_likelihood],
            thetas=theta,
            xs=x,
            ys=None,
            batch_size=batch_size,
            initial_learning_rate=initial_learning_rate,
            final_learning_rate=final_learning_rate,
            n_epochs=n_epochs,
            early_stopping=early_stopping,
            learning_curve_folder=learning_curve_folder,
            learning_curve_filename=learning_curve_filename
        )

    def save(self, filename):
        torch.save(self.maf, filename + '.pt')

    def predict_density(self, theta, x, log=False):
        log_likelihood = self.maf.predict_log_likelihood(tensor(theta), tensor(x)).detach().numpy()

        if log:
            return log_likelihood
        return np.exp(log_likelihood)

    def predict_ratio(self, theta0, theta1, x, log=False):
        log_likelihood_theta0 = self.maf.predict_log_likelihood(tensor(theta0), tensor(x)).detach().numpy()
        log_likelihood_theta1 = self.maf.predict_log_likelihood(tensor(theta1), tensor(x)).detach().numpy()

        if log:
            return log_likelihood_theta0 - log_likelihood_theta1
        return np.exp(log_likelihood_theta0 - log_likelihood_theta1)

    def predict_score(self, theta, x):
        score = self.maf.predict_score(tensor(theta), tensor(x)).detach().numpy()

        return score

    def generate_samples(self, theta):
        samples = self.maf.generate_samples(theta).detach().numpy()
        return samples
