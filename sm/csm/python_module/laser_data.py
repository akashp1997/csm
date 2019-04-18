import time
import collections
import laser_data_inline
import numpy as np
import math

correspondence = collections.namedtuple("correspondence", ['valid', 'j1', 'j2', 'type', 'dist2_j1'])

point2d = collections.namedtuple("point2d", ['p','rho','phi'])

laser_data = collections.namedtuple("laser_data", ['nrays','min_theta','max_theta','theta','valid','readings',\
'cluster','alpha','cov_alpha','alpha_valid','readings_sigma',\
'true_alpha','corr','true_pose','odometry','estimate','points','points_w','tv','hostname','up_bigger',\
'up_smaller','down_bigger','down_smaller'])

def alloc_dtype_array(n, de, dtype=np.float64):
    arr = np.empty(n,dtype=dtype)
    arr.fill(de)
    return arr

def ld_alloc(nrays):
    ld = {}
    ld["nrays"] = nrays
    ld["valid"] = alloc_dtype_array(nrays, False, dtype=np.bool)

    ld["max_theta"] = np.NaN
    ld["min_theta"] = np.NaN

    ld["readings"] = alloc_dtype_array(nrays, np.NaN)
    ld["readings_sigma"] = alloc_dtype_array(nrays, np.NaN)
    ld["theta"] = alloc_dtype_array(nrays, np.NaN)

    ld["cluster"] = alloc_dtype_array(nrays, -1, dtype=np.int64)
    ld["alpha"] = alloc_dtype_array(nrays, np.NaN)
    ld["cov_alpha"] = alloc_dtype_array(nrays, np.NaN)
    ld["alpha_valid"] = alloc_dtype_array(nrays, False, dtype=np.bool)

    ld["true_alpha"] = alloc_dtype_array(nrays, np.NaN)

    ld["up_bigger"] = alloc_dtype_array(nrays, 0, dtype=np.int64)
    ld["up_smaller"] = alloc_dtype_array(nrays, 0, dtype=np.int64)
    ld["down_bigger"] = alloc_dtype_array(nrays, 0, dtype=np.int64)
    ld["down_smaller"] = alloc_dtype_array(nrays, 0, dtype=np.int64)

    _corr = correspondence(valid=False,j1=-1,j2=-1, type=0, dist2_j1=0)
    ld["corr"] = alloc_dtype_array(nrays, _corr, dtype=correspondence)
    ld["odometry"] = alloc_dtype_array(3, np.NaN)
    ld["estimate"] = alloc_dtype_array(3, np.NaN)
    ld["true_pose"] = alloc_dtype_array(3, np.NaN)

    _pt = point2d(p=[np.NaN, np.NaN], rho=np.NaN, phi=np.NaN)
    ld["points"] = alloc_dtype_array(nrays, _pt, point2d)
    ld["points_w"] = alloc_dtype_array(nrays, _pt, point2d)

    ld["hostname"] = "CSM"
    ld["tv"] = None
    return laser_data(**ld)


def ld_alloc_new(nrays):
    ld = ld_alloc(nrays)
    return ld

def ld_dealloc(ld):
    del ld

def ld_free(ld):
    ld_dealloc(ld)

def ld_compute_cartesian(ld):
    def temp(pt):
        return point2d(p=pt,rho=np.NaN,phi=np.NaN)

    cos = np.vectorize(math.cos)
    sin = np.vectorize(math.sin)
    _pts = numpy.hstack(numpy.multiply(cos(ld.theta), ld.readings), numpy.multiply(sin(ld.theta), ld.readings))
    _pt = point2d()
    temp = np.vectorize(temp)
    return temp(_pts)

def ld_compute_world_coords(ld, pose):
    cos_theta = math.cos(pose[2])
    sin_theta = math.sin(pose[2])
    def temp(x):
        x0 = x.p[0]
        y0 = x.p[1]
        #if not laser_data_inline.ld_valid_ray(ld,count):
        #    return None
        if np.isnan(x.p[0]) or np.isnan(x.p[1]):
            return None
            #raise SMERROR()
        x.p[0] = cos_theta*x0-sin_theta*y0+pose[0]
        x.p[1] = sin_theta*x0+cos_theta*y0+pose[1]
        x.rho = math.sqrt(x.p[0]**2+x.p[1]**2)
        x.phi = math.atan2(x.p[1], x.p[0])
        return x

    temp = np.vectorize(temp)
    return ld._replace(points_w=temp(ld.points))


def ld_create_jump_tables(ldp):
    pass

def ld_corr_hash(ld):
    hash = 0
    for i in range(nrays):
        if laser_data_inline.ld_valid_corr(ld, i):
            str = ld.corr[i].j1+1000*ld.corr[i].js
        else:
            str = -1
        if((i&1)==0):
            hash = hash ^ ((hash<<7)^(str)^(hash>>3))
        else:
            hash = hash ^ ~((hash<<11)^(str)^(hash>>5))

    return hash & 2147483647

def ld_num_valid_correspondences(ld):
    temp = np.vectorize(lambda x: x.valid)
    return np.count_nonzero(temp(ld.corr))

def ld_valid_fields(ld):
    if(ld==None):
        return False
        #SMERROR
    min_nrays = 10
    max_nrays = 10000
    if ld.nrays<min_nrays or ld.nrays>max_nrays:
        #SMERROR
        return False
    if np.isnan(ld.min_theta) or np.isnan(ld.max_theta):
        #SMERROR
        return False

    min_fov = math.radians(20.0)
    max_fov = 2.01*math.pi
    fov = ld.max_theta-ld.min_theta
    if fov<min_fov or fov>max_fov:
        #SMERROR
        return False
    if(abs(ld.max_theta)-ld.theta[-1]>10**8):
        #SMERROR
        return False

    min_reading = 0
    max_reading = 100
    for i in range(ld.nrays):
        th = ld.theta[i]
        if(ld.valid[i]):
            r = ld.readings[i]
            if np.isnan(r) or np.isnan(th):
                #SMERROR
                return False
            if not (min_reading<r and r<max_reading):
                #SMERROR
                return False
        else:
            if np.isnan(th):
                #SRMERROR
                return False
            if ld.cluster[i]!=-1:
                #SMERROR
                return False
        if ld.cluster[i]<-1:
            #SMERROR
            return False
        if np.isnan(ld.readings_sigma[i]) and ld.readings_sigma[i]<0:
            #SMERROR
            return False
    num_valid = np.count_nonzero(ld.valid)
    num_invalid = ld.nrays-num_valid
    if num_valid<ld.nrays*0.1:
        #SRMERROR
        return False
    return True

def ld_simple_clustering(ld, threshold):
    pass

def ld_compute_orientation(ld, size_neighbourhood, sigma):
    pass

def ld_read_smart(file):
    pass

def ld_read_smart_string(string):
    pass

def ld_read_next_laser_carmen(line):
    pass

def ld_read_all(file, array, num):
    pass

def ld_read_some_scans(file, array, num, interval):
    pass

def ld_write_as_carmen(ld, stream):
    pass

def ld_write_format(ld, stream, out_format):
    pass

def possible_interval(p_i_w, laser_sens, max_angular_correction_deg, max_linear_correction, fro, to, start_cell):
    pass

a = ld_alloc(5)
ld_compute_world_coords(a, [0,0,1])
ld_free(a)
