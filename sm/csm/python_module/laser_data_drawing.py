import enum
import collections

import laser_data

oriented_bbox = collections.namedtuple("oriented_bbox", ["pose", "size"])

bbfind_imp = collections.namedtuple("bbfind_imp", [])

stroke_sequence = collections.namedtuple("stroke_sequence", ["begin_new_stroke", "end_stroke", "valid", "p"])

class ld_reference(enum.Enum):
    Invalid = 0
    Odometry = 1
    Estimate = 2
    True_pose = 3

def ld_reference_to_string(ld_ref):
    return ld_reference(ld_ref).name

def ld_string_to_reference(string):
    return ld_reference[string].value

def ld_get_reference_pose_silent(ld, ld_ref):
    pass

def ld_get_reference_pose(ld, use_ref):
    pass

def ld_read_some_scans_distance(file, array, num, which, d_xy, d_th):
    pass

def ld_get_bounding_box(ld, bb_min, bb_max, pose, horizon):
    for i in 

def lda_get_bounding_box(ld, nld, bb_min, bb_max, offset, use_ref, horizon):
    pass

def oriented_bbox_compute_corners(bb, ul, ur, ll, lr):
    pass

def ld_get_oriented_bbox(ls, horizon, bb):
    pass

def bbfind_new():
    pass

def bbfind_add_point(bbfind, p):
    pass

def bbfind_add_point2(bbfind, x, y):
    pass

def bbfind_add_bbox(bbfind, bb):
    pass

def bbfind_compute(bbfind, bb):
    pass

def bbfind_free(bbfind):
    pass

def compute_stroke_sequence(ld, stroke_seq, horizon, connect_thres):
    pass
