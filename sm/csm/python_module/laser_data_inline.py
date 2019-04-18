import numpy as np

def ld_valid_ray(ld, i):
    return i>=0 and i<ld.nrays and ld.valid[i]

def ld_valid_alpha(ld, i):
    return ld.alpha_valid[i]!=False

def ld_set_null_correspondence(ld, i):
    ld.corr[i].valid = False
    ld.corr[i].j1 = -1
    ld.corr[i].j2 = -1
    ld.corr[i].dist2_j1 = np.NaN

def ld_set_correspondence(ld, i, j1, j2):
    ld.corr[i].valid = True
    ld.corr[i].j1 = j1
    ld.corr[i].j2 = j2

def ld_next_valid(ld, i, dir):
    j = i+dir
    while(j<ld.nrays and j>=0 and not ld_valid_ray(ld,j)):
        j += dir
    if ld_valid_ray(ld,j):
        return j
    return -1

def ld_next_valid_up(ld, i):
    return ld_next_valid(ld, i, 1)

def ld_next_valid_down(ld, i):
    return ld_next_valid(ld, i, -1)

def ld_valid_corr(ld, i):
    return ld.corr[i].valid
