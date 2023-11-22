from scipy.stats import exponnorm
from scipy.ndimage import gaussian_filter
import numpy as np
import pickle
import globalpars
import matplotlib.pyplot as plt
from os.path import basename
from confsmooth import confsmooth


def get_data(pkl_file):
	with open(pkl_file, 'rb') as f:
		data = pickle.load(f)
	return data.frbname, data.tmsarr, data.it, data.tresms, data.irms


def exgauss(x, *args):
	'''
	Returns the single value f(x) of the sum of n exGaussian functions with individual
	params listed in args, followed by a single param ts.
	eg. exgauss(x, a0, u0, sd0, a1, u1, sd1, ts)
	'''
	_exgauss = lambda x, a, u, sd, ts: a * exponnorm.pdf(x, ts / sd, loc=u, scale=sd)
	return sum(_exgauss(x, *args[i:i+3], args[-1]) for i in range(0, len(args)-1, 3))


def integral(x, *args):
	'''
	Integral from -inf to x of the sum of exGaussians.
	'''
	single_integral = lambda x, a, u, sd, ts: a * exponnorm.cdf(x, ts / sd, loc=u, scale=sd)
	return sum(single_integral(x, *args[i:i+3], args[-1]) for i in range(0, len(args)-1, 3))


def raw_burst_range(ys, area=globalpars.RAW_CENTRE_AREA, extra_width=globalpars.RAW_EXTRA_WIDTH):
	'''
	Attempt to extract the FRB range from the raw data. Finds the middle range
	containing `area` proportion of total area under the curve.

	Finally extends the range by `extra_width` on each side.
	'''
	# smooth = confsmooth(ys, rms)
	total_area = np.trapz(ys)
	low_area = (1 - area) / 2 * total_area
	high_area = (1 + area) / 2 * total_area
	i = 0
	while np.trapz(ys[:i]) < low_area: i += 1
	low = i
	while np.trapz(ys[:i]) < high_area: i += 1
	width = (i - low) * extra_width
	return max(0, low - width), min(len(ys), i + width)


def model_burst_range(xs, params, area=globalpars.MODEL_CENTRE_AREA):
	'''
	Get the burst range of a fitted curve by iterating through xs and finding the
	central range containing `width` proportion of the total area under the curve.
	'''
	total_area = integral(xs[-1], *params)
	low_area = (1 - area) / 2 * total_area
	high_area = (1 + area) / 2 * total_area

	i = 0
	while integral(xs[i], *params) < low_area: i += 1
	low = i
	while integral(xs[i], *params) < high_area: i += 1

	return low, i


def rsquared(xs, ys, params):
	'''
	Returns R squared value for a set of parameters.
	'''
	residuals = ys - np.array([exgauss(x, *params) for x in xs])
	ss_res = np.sum(residuals ** 2)
	ss_tot = np.sum((ys - np.mean(ys)) ** 2)
	return 1 - (ss_res / ss_tot)


def adjusted_rsquared(xs, ys, params):
	'''
	Returns adjust R squared value for a set of parameters.
	'''
	rs = rsquared(xs, ys, params)
	return 1 - (1 - rs) * (len(xs) - 1) / (len(xs) - len(params) - 1)


def plot_single_fit(xs, ys, params):
	'''
	Plot fit on a separate figure.
	'''
	fig, ax = plt.subplots(1, 1)
	ax.plot(xs, ys, color='red', label='Smoothed FRB')
	ax.plot(xs, [exgauss(x, *params) for x in xs], color='black', label='Estimated params')
	fig.suptitle('Estimated Parameters')
	fig.legend()


def print_summary(data):
	opt_n = data['optimum']
	rsquared = data['data'][opt_n]['adjusted_R^2']
	cond = data['data'][opt_n]['condition']
	opt_timescale = data['data'][opt_n]['timescale']
	timescale_uncertainty = data['data'][opt_n]['timescale_uncertainty']
	opt_burst_width = data['data'][opt_n]['burst_width']

	print(f'Optimum N: {opt_n}')
	print(f'Adjusted R^2: {rsquared}')
	print(f'Condition number: {cond}')
	print(f'Timescale: {opt_timescale}')
	print(f'Timescale uncertainty: {timescale_uncertainty}')
	print(f'Width: {opt_burst_width}')


def get_frb(input):
	'''
	Exract the FRB name from an input file.
	'''
	name = basename(input)
	return name[:name.index(".")]
