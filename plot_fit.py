'''
Visualises the curve fitted FRBs.
'''

import numpy as np
import matplotlib.pyplot as plt
from utils import *
import json


def plot_single_fit(xs, ys, params):
	'''
	Plot fit model on a separate figure. Used for displaying the initial params
	against the raw FRB.
	'''
	fig, ax = plt.subplots(1, 1)
	ax.plot(xs, ys, color='red', label='Smoothed FRB')
	ax.plot(xs, [exgauss(x, *params) for x in xs], color='black', label='Estimated params')
	fig.suptitle('Estimated Parameters')
	fig.legend()


def plot_residuals(xs, ys, params, rms, ax):
	'''
	Plot residuals / RMS as a scatter plot.
	'''
	residuals = ys - np.array([exgauss(x, *params) for x in xs])
	ax.scatter(xs, residuals / rms, color='black', alpha=0.3)
	ax.set_ylabel('Residuals / RMS')


def _plot(xs, ys, data, rms, n, low_i):
	'''
	Plot the sum of exgausses with given params. Also plot individual exgauss components and original FRB.
	'''
	fig, ax = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [1, 2]})
	fig.subplots_adjust(hspace=0)

	params = data['Params']
	low, high = data['Burst range']

	plot_residuals(xs, ys, params, rms, ax[0])
	
	# FRB
	ax[1].plot(xs, ys, label='FRB', color='red')
	
	# fitted curve
	ax[1].plot(xs, exgauss(xs, *params), label=f'N={n}', color='black')
	
	# components
	for i in range(0, len(params)-1, 3):
		ax[1].plot(xs, exgauss(xs, *params[i:i+3], params[-1]), linestyle='dotted', color='blue')

	# burst width
	ax[1].axvline(xs[low - low_i], color='green')
	ax[1].axvline(xs[high - low_i], color='green')
	
	ax[1].set_ylabel('Intensity')
	plt.xlabel('Time (ms)')
	fig.legend()


def plot_fitted(xs, ys, rms, data, n, show_initial=False):
	'''
	Plots the fitted curved found in the json data. Can be filtered with an optional parameter ns: a list of ns to plot.
	'''
	low, high = data['range']
	xs, ys = xs[low:high], ys[low:high]
	
	d = data['data'][n]

	if show_initial:
		plot_single_fit(xs, ys, d['Initial params'])

	_plot(xs, ys, d, rms, n, low)


if __name__ == '__main__':
	from argparse import ArgumentParser

	a = ArgumentParser()
	a.add_argument('--show-initial', action='store_true')
	a.add_argument('--show', action='store_true')
	a.add_argument('inputs', nargs='*', default=get_files('data'))

	args = a.parse_args()

	for input in args.inputs:
		frb = get_frb(input)
		output = f'output/{frb}_out.json'

		frb_data = get_data(input)

		with open(output, 'r') as f:
			data = json.load(f)

		n = data['optimum']

		plot_fitted(frb_data.tmsarr, frb_data.it, frb_data.irms, data, n, args.show_initial)
			
		if not (args.show or args.show_initial):
			plt.savefig(f'figs/fits/{frb}')
	
	if args.show or args.show_initial:
		plt.show(block=True)