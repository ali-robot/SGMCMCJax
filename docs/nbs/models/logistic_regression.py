
import numpy as np
import jax.numpy as jnp
from jax import jit, grad, value_and_grad, vmap, random
from jax.scipy.special import logsumexp
import warnings

#ignore by GPU/TPU message (generated by jax module)
warnings.filterwarnings("ignore", message='No GPU/TPU found, falling back to CPU.')


def genCovMat(key, d, rho):
    Sigma0 = np.diag(np.ones(d))
    for i in range(1,d):
        for j in range(0, i):
            Sigma0[i,j] = (random.uniform(key)*2*rho - rho)**(i-j)
            Sigma0[j,i] = Sigma0[i,j]

    return jnp.array(Sigma0)


def logistic(theta, x):
    return 1/(1+jnp.exp(-jnp.dot(theta, x)))

batch_logistic = jit(vmap(logistic, in_axes=(None, 0)))
batch_benoulli = vmap(random.bernoulli, in_axes=(0, 0))

def gen_data(key, dim, N):
    """
    Generate data with dimension `dim` and `N` data points

    Parameters
    ----------
    key: uint32
        random key
    dim: int
        dimension of data
    N: int
        Size of dataset

    Returns
    -------
    theta_true: ndarray
        Theta array used to generate data
    X: ndarray
        Input data, shape=(N,dim)
    y_data: ndarray
        Output data: 0 or 1s. shape=(N,)
    """
    key, subkey1, subkey2, subkey3 = random.split(key, 4)
    rho = 0.4
    print(f"generating data, with N={N} and dim={dim}")
    theta_true = random.normal(subkey1, shape=(dim, ))*jnp.sqrt(10)
    covX = genCovMat(subkey2, dim, rho)
    X = jnp.dot(random.normal(subkey3, shape=(N,dim)), jnp.linalg.cholesky(covX))

    p_array = batch_logistic(theta_true, X)
    keys = random.split(key, N)
    y_data = batch_benoulli(keys, p_array).astype(jnp.int32)
    return theta_true, X, y_data


@jit
def loglikelihood(theta, x_val, y_val):
    return -logsumexp(jnp.array([0., (1.-2.*y_val)*jnp.dot(theta, x_val)]))

@jit
def logprior(theta):
    return -(0.5/10)*jnp.dot(theta,theta)
