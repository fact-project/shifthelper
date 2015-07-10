# -*- encoding:utf-8 -*-
"""
This program calculates B_01, S_B_01, PDF("P_lambda"), CDF("C_lambda"),
together with interesting points on the PDF, such as 99% credible UL ("l_99")
and the 16% and 84% credible UL for calculating the central interval
containing 68% signal posterior probability (for error signal estimation)

All methods based on:

    Max L. Knoetig: Signal Discovery, Limits, and Uncertainties
    with Sparse On/Off Measurements: An Objective Bayesian Analysis;
    The Astrophysical Journal, 790, 2, 106; 2014
    http://stacks.iop.org/0004-637X/790/i=2/a=106


    Max L. Ahnen: On the On-Off Problem:
    An Objective Bayesian Analysis;
    InProceedings, ICRC 2015, The Hague

-----------------------
Author, Date: Max L. Ahnen, Jul.2015


A note:
This method was checked roughly up to non=120, noff=200 @ alpha = 0.1
You need to calculate higher numbers together with smaller alpha?
use MATHEMATICA -> thousands of counts possible, using
higher precision calculations on the special functions, see:
http://community.wolfram.com/groups/-/m/t/102242?p_p_auth=K8r5Y8QR
"""
from __future__ import print_function, division
from numpy import frompyfunc, arange
from scipy.optimize import fminbound
from sympy.mpmath import (
    hyperu,
    mp,
    sqrt,
    pi,
    atan,
    hyp2f1,
    gamma,
    erfinv,
    rgamma,
    exp,
    power,
    quad,
    findroot,
)


# set a sufficiently good accuracy for mpmath
mp.dps = 50


def B_01(Non, Noff, alpha):
    '''
    define Bayes factor, meaning the odds of background hypothesis over the
    signal hypothesis.

    '''
    # gamma, delta, c1/c2
    Nges = Non + Noff
    gam = (1 + 2 * Noff) * alpha ** (0.5 + Nges) * gamma(0.5 + Nges)
    delta = (2 * (1 + alpha)**Nges * gamma(1+Nges) *
             hyp2f1(0.5 + Noff, 1 + Nges, 1.5 + Noff, (-1 / alpha)))
    c1_c2 = sqrt(pi) / (2 * atan(1 / sqrt(alpha)))

    return gam / (c1_c2 * delta)


def P_lambda(lambda_s, Non, Noff, alpha):
    '''
    This is the marginalized signal parameter posterior.
    The method is vectorized, in order to plot it faster (with matplotlib).
    '''
    # make a vectoriyed version of hyperu
    hyperu_vec = frompyfunc(hyperu, 3, 1)
    exp_vec = frompyfunc(exp, 1, 1)
    power_vec = frompyfunc(power, 2, 1)
    # rgamma_vec = frompyfunc(rgamma,1,1)

    n1 = Non + Noff
    n2 = Noff + 0.5
    n3 = n1 + 1
    n4 = n2 + 1

    buf1 = exp_vec(-lambda_s) * power_vec(lambda_s, n1) * rgamma(n1 + 1)
    buf2 = hyperu_vec(n2, n3, lambda_s * (1. + 1. / alpha))
    buf3 = hyp2f1(n2, n3, n4, (-1. / alpha)) * rgamma(n4)

    # print(buf1, buf2, buf3)

    return 1./buf3*buf1*buf2


def C_lambda(
        lambda_s,
        Non,
        Noff,
        alpha,
        maxdeg=4,
        err=True,
        meth='gauss-legendre',
        ):
    '''
    The cumulative distribution function of the signal posterior.
    It uses Gauss-Legendre quadrature (optionally whatever mpmath.quad
    can offer), in order to calculate the definite integral on the
    interval [0,lambda_s].
    '''
    return quad(
        lambda x: P_lambda(x, Non, Noff, alpha),
        [0, lambda_s],
        maxdegree=maxdeg,
        error=err,
        method=meth)


def S_B_01(Non, Noff, alpha):
    '''
    calculate the bayesian z-value via the bayes factor, truncated
    to a reasonable number count region
    '''
    buf = 1-B_01(Non, Noff, alpha)
    if buf < -1.0:
        buf = -1.0
    # print(buf)
    return sqrt("2")*erfinv(buf)


def l_star(Non, Noff, alpha):
    '''
    this function shall find the local maximum of the signal
    posterior using Brent's method and a good guess of the
    bounds
    '''
    sigma = sqrt(alpha*alpha*Noff + Non)
    lstar = 0.0-alpha*Noff+Non

    if lstar <= 0.0:
        return 0.0

    lmin = 1e-11 if (lstar - sigma) < 0 else (lstar - sigma)
    lmax = lstar + sigma

    # print(lmin, lstar, lmax)
    res = fminbound(lambda x: P_lambda(x, Non, Noff, alpha)*-1.0, lmin, lmax)
    return res


def l_99(Non, Noff, alpha):
    '''
    this function shall find the 99% signal
    posterior UL using the secant method and a good guess of the
    starting point '''
    sigma = sqrt(alpha*alpha*Noff + Non)
    lstar = 0.0-alpha*Noff+Non

    # lmin = 1e-11 if (lstar - sigma) < 0 else (lstar - sigma)
    lmax = 1e-11 if (lstar + 2*sigma) < 0 else (lstar + 2*sigma)
    guess = 3. + lmax
    # print(guess)

    b = findroot(
        lambda x: C_lambda(x, Non, Noff, alpha)[0]-0.99,
        guess,
        solver='secant',
        tol=1e-8)
    return b


def l_84(Non, Noff, alpha):
    '''
    this function shall find the 84% signal
    posterior UL using the secant method and a good guess of the
    starting point
    '''
    sigma = sqrt(alpha*alpha*Noff + Non)
    lstar = 0.0-alpha*Noff+Non

    # lmin = 1e-11 if (lstar - sigma) < 0 else (lstar - sigma)
    lmax = 1e-11 if (lstar + 1.*sigma) < 0 else (lstar + 1.*sigma)
    guess = 1. + lmax
    # print(sigma, lstar, lmax, guess)

    b = findroot(
        lambda x: C_lambda(x, Non, Noff, alpha)[0] - 0.84,
        guess,
        solver='secant',
        tol=1e-8)
    return b


def l_16(Non, Noff, alpha):
    '''
    this function shall find the 16% signal
    posterior UL using the secant method and a good guess of the
    starting point
    '''
    sigma = sqrt(alpha*alpha*Noff + Non)
    lstar = 0.0-alpha*Noff+Non

    # lmin = 1e-11 if (lstar - sigma) < 0 else (lstar - sigma)
    lmax = 1e-11 if (lstar - 1.*sigma) < 0 else (lstar - 1.*sigma)
    guess = 0.2 + lmax
    # print(sigma, lstar, lmax, guess)

    b = findroot(
        lambda x: C_lambda(x, Non, Noff, alpha)[0] - 0.16,
        guess,
        solver='secant',
        tol=1e-8)
    return b

# run the above methods to test them, if called directly
if __name__ == "__main__":
    import pylab as plt

    # try and plot the thing

    n_on = 29
    n_off = 34
    alpha = 1./5.
    print("Measurement: N_on, N_off, alpha, B_01, S_B_01, signal_estimate")
    l_99_buf = l_99(n_on, n_off, alpha)
    significance = S_B_01(n_on, n_off, alpha)
    if significance > 3.0:
        l_star_buf = l_star(n_on, n_off, alpha)
        l_84_buf = l_84(n_on, n_off, alpha)
        l_16_buf = l_16(n_on, n_off, alpha)
        print("{on:d}, {off:d}, {al:.3f}, {B:.3e}, " +
              "{S:.3f}, {ls:.3f}+{lu:.3f}-{ll:.3f}".format(
                  on=n_on, off=n_off, al=alpha,
                  B=float(B_01(n_on, n_off, alpha)),
                  S=float(significance),
                  ls=float(l_star_buf),
                  lu=float(l_84_buf - l_star_buf),
                  ll=float(l_star_buf - l_16_buf))
              )
    else:
        print("{on:d}, {off:d}, {al:.3f}, {B:.3e}, {S:.3f}, <{l99:.3f}".format(
            on=n_on, off=n_off, al=alpha,
            B=float(B_01(n_on, n_off, alpha)),
            S=float(significance),
            l99=float(l_99_buf)),
        )
    # plot the pdf
    x_range = arange(0, 2 * float(l_99_buf), 0.1)
    y_range = P_lambda(x_range, n_on, n_off, alpha)
    plt.clf()
    plt.plot(x_range, y_range)
    plt.show()
