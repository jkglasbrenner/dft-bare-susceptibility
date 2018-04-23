# -*- coding: utf-8; -*-

# Modules
from pathlib import Path
import csv
import re
import gzip
import numpy as np


# Functions
def find_regexp(file_path, regexp):
    with gzip.open(str(file_path), 'rt') as in_file:
        tmp_match = regexp.findall(in_file.read())

    return tmp_match


def extract_from_dx_file(file_path):
    # Convert filepath string to Path object
    file_path = Path(file_path)

    # Extract from .dx file
    nx, ny, nz = find_qmesh_pts(file_path)
    q_vectors = find_qmesh_vectors(file_path)
    origin = find_origin(file_path)
    shape = find_shape(file_path)
    data_string = find_data(file_path)

    # Create dx data array
    data_list = create_dx_data_list(data_string, shape)

    # Convert dx format to generic numpy array format
    data_array = build_data_array(nx, ny, nz, shape, data_list)

    # Output
    return q_vectors, origin, data_array


def find_qmesh_pts(file_path):
    # Create regexp
    regexp = re.compile(r'(?:object\s+1.*?)(\d+)(?:\s+)'
                        '(\d+)(?:\s+)(\d+)')

    # Open and run regexp
    tmp_match = find_regexp(file_path, regexp)

    # Extract kpts
    nx, ny, nz = tmp_match[0]

    # Output
    return int(nx), int(ny), int(nz)


def find_qmesh_vectors(file_path):
    # Create regexp
    re_num = r'([+-]?\d+\.?\d+(?:[eE][-+]?\d+)?)'
    re_exp = (r'(?:delta\s+)' + re_num + r'(?:\s+)'
              + re_num + r'(?:\s+)' + re_num)
    regexp = re.compile(re_exp)

    # Open and run regexp
    tmp_match = find_regexp(file_path, regexp)

    # Extract kmesh
    qx = tuple(float(item) for item in tmp_match[0])
    qy = tuple(float(item) for item in tmp_match[1])
    qz = tuple(float(item) for item in tmp_match[2])

    # Convert to numpy array
    q_vectors = np.array([qx, qy, qz])

    # Output
    return q_vectors


def find_origin(file_path):
    # Create regexp
    re_num = r'([+-]?\d+\.?\d+(?:[eE][-+]?\d+)?)'
    re_exp = (r'(?:origin\s+)' + re_num + r'(?:\s+)'
              + re_num + r'(?:\s+)' + re_num)
    regexp = re.compile(re_exp)

    # Open and run regexp
    tmp_match = find_regexp(file_path, regexp)

    # Extract origin
    origin = tuple(float(item) for item in tmp_match[0])

    # Output
    return origin


def find_shape(file_path):
    # Create regexp
    re_exp = r'(?:object\s+3.*?shape\s+)(\d+)'
    regexp = re.compile(re_exp)

    # Open and run regexp
    tmp_match = find_regexp(file_path, regexp)

    # Extract kmesh
    shape = tmp_match[0]

    # Output
    return int(shape)


def find_data(file_path):
    # Create regexp
    regexp = re.compile(r'(?:data follows.*?\n)'
                        '((?:.*?\n)+?)(?:\s*object)')

    # Open and run regexp
    tmp_match = find_regexp(file_path, regexp)

    # Output
    return tmp_match[0]


def create_dx_data_list(string, shape):
    # Create regexp
    re_exp = r'([+-]?\d+\.?\d+(?:[eE][-+]?\d+)?)'
    regexp = re.compile(re_exp)

    # Run regexp
    tmp_match = regexp.findall(string)

    # Create lists
    my_list = []
    tmp_list = []
    i = 1
    for item in tmp_match:
        if i <= shape:
            tmp_list.append(float(item))
            i = i + 1
        if i > shape:
            my_list.append(tmp_list)
            tmp_list = []
            i = 1

    # Convert to numpy array
    my_list = np.array(my_list)

    # Output
    return my_list


def build_data_array(nx, ny, nz, num_items, in_array):
    # Allocate numpy array
    tmp_array = np.zeros([num_items, nx, ny, nz])

    # Count entries in in_array
    slice_index = int(0)
    end_index = slice_index + nz

    # Assign to array
    for i in range(nx):
        for j in range(ny):
            for n in range(num_items):
                tmp_array[n, i, j, :] = in_array[slice_index:end_index, n]
            slice_index = slice_index + nz
            end_index = slice_index + nz

    # Output array
    return tmp_array


def write_file(data_array, qx, qy, qz, origin, outfilepath, data_format="csv"):
    # Grab data_array dimensions
    nx, ny, nz, shape = data_array.shape

    # Open file
    if data_format == "dx":
        with open(str(outfilepath), 'wt') as out_file:
            write_header(nx, ny, nz, qx, qy, qz, origin, shape, out_file)
            write_data_columns(data_array, shape, nx, ny, nz, out_file)
            write_footer(out_file)

    elif data_format == "csv":
        with open(str(outfilepath), 'w', newline="") as out_file:
            write_csv_format(data_array, shape, nx, ny, nz, out_file)

    else:
        print("{0} is not a valid data format, exiting...".format(data_format))


def write_csv_format(data_array, shape, nx, ny, nz, outfile):
    fieldnames = ["band_index", "kx", "ky", "kz", "energy"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames,
                            quoting=csv.QUOTE_MINIMAL)

    writer.writeheader()
    for kx in range(nx):
        for ky in range(ny):
            for kz in range(nz):
                for band_index in range(shape):
                    data_row = {
                        "band_index": band_index,
                        "kx": kx,
                        "ky": ky,
                        "kz": kz,
                        "energy": data_array[kx, ky, kz, band_index]
                    }
                    writer.writerow(data_row)


def write_data_columns(data_array, shape, nx, ny, nz, outfile):
    # Counters
    xx = 0
    yy = 0
    zz = 0

    # Loop for printing
    for i in range(nx):
        for j in range(ny):
            zz = zz_loop(data_array, shape, nz, xx, yy, zz, outfile)
            yy = iterate_counter(yy, ny)
        xx = iterate_counter(xx, nx)


def zz_loop(data_array, shape, nz, xx, yy, zz, outfile):
    # Set up output format
    string = ''
    for n in range(shape):
        string = string + '{{i{0}:12.6f}}'.format(n)

    # Printing loop
    for k in range(nz):
        line_dict = dict()
        for n in range(shape):
            line_dict["i" + str(n)] = data_array[xx, yy, zz, n]
        tmp_line = string.format(**line_dict)
        print(tmp_line, file=outfile)
        zz = iterate_counter(zz, nz)

    # Return counter
    return zz


def write_header(nx, ny, nz, qx, qy, qz, origin, shape, outfile):
    nitems = int(nx * ny * nz)
    header = (' object 1 class gridpositions counts  {0:>11} {1:>11} {2:>11}\n'
              'origin {3:14.8f} {4:14.8f} {5:14.8f}\n'
              'delta      {6:11.8f} {7:11.8f} {8:11.8f}\n'
              'delta      {9:11.8f} {10:11.8f} {11:11.8f}\n'
              'delta      {12:11.8f} {13:11.8f} {14:11.8f}\n'
              ' object 2 class gridconnections counts  {15:>11} '
              '{16:>11} {17:>11}\n'
              ' object 3 class array type float rank 1 shape  {18:>11}  items'
              '  {19:>11}\n'
              '  data follows')
    output_str = header.format(nx, ny, nz,
                               origin[0], origin[1], origin[2],
                               qx[0], qx[1], qx[2],
                               qy[0], qy[1], qy[2],
                               qz[0], qz[1], qz[2],
                               nx, ny, nz,
                               shape, nitems)

    # Write header
    print(output_str, file=outfile)


def write_footer(outfile):
    footer = (' object "regular positions regular connections" class '
              'field\n'
              ' component "positions" value 1\n'
              ' component "connections" value 2\n'
              ' component "data" value 3\n'
              ' end')

    # Write footer
    print(footer, file=outfile)


def test_counter(count, qmax):
    if count >= qmax:
        count = int(0)
        return count
    else:
        return count


def iterate_counter(count, qmax):
    count += int(1)
    return test_counter(count, qmax)


def expand_data_range(data_array):
    # Calculate expanded parameters
    in_nx, in_ny, in_nz = data_array.shape
    nx = in_nx + 1
    ny = in_ny + 1
    nz = in_nz + 1

    # Allocate array for expanded data
    new_data = np.zeros([nx, ny, nz])

    # Fill existing array
    new_data[:-1, :-1, :-1] = data_array

    # Fill in end of Brillouin zone
    end_bz_fill(new_data, nx, ny, nz)

    # Return results
    return new_data


def end_bz_fill(new_data, nx, ny, nz):
    for xx in range(nx):
        for yy in range(ny):
            for zz in range(nz):
                i = xx
                j = yy
                k = zz
                if (xx == (nx - 1)) or (yy == (ny - 1)) or (zz == (nz - 1)):
                    if xx == (nx - 1):
                        i = 0
                    if yy == (ny - 1):
                        j = 0
                    if zz == (nz - 1):
                        k = 0
                    new_data[xx, yy, zz] = new_data[i, j, k]
