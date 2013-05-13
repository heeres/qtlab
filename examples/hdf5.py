"""
Example to illustrate the usage of the hdf5_data module;
To check out the resulting file, you can use, besides python,
the HDFView Program from the HDF group (hdfgroup.com).

About HDF5 implementation in python see h5py.alfven.org.

Latest version: 2012/12/26, Wolfgang Pfaff <wolfgangpfff at gmail dot com>
"""

import hdf5_data as h5
import numpy as np

### Direct access to hdf5 container

# create data; follows the data storage scheme of qtlab
dat = h5.HDF5Data(name='data_number_one')

# this function is a simple wrapper for the h5py method of the same name
print 'create our first dataset'
dset1 = dat.create_dataset('first set', (5,5), 'i')
dset1[...] = 42
print dset1 # this is the dataset object
print dset1.value # this is a numpy array

# simpler access (equivalent)
print ''
print 'again...'
print dat['/first set']

# create something in a group, by simple access (there's also a create_group
# method that's a simple wrapper for the h5py method).
print ''
print 'more data...'

# On new versions of h5py you don't have to explicitly create the groups,
# but you can set an array in any group you like.
arr = np.arange(16).reshape((4,4))
g1 = dat.create_group('my first group')
g2 = g1.create_group('my first subgroup')
dat['/my first group/my first subgroup/an array'] = arr
print dat['/my first group']
print dat['/my first group/my first subgroup']
print dat['/my first group/my first subgroup/an array'].value

# set some metadata
# any stuff can be attribute to data sets and groups; any kind of data that
# fits into numpy arrays can be stuffed in there.
dat['/my first group'].attrs['description'] = 'an utterly pointless group'
dat['/my first group'].attrs['yo mama'] = 'probably fat'
dat['/my first group/my first subgroup/an array'].\
        attrs['unit'] = 'TT'
dat['/my first group/my first subgroup/an array'].\
        attrs['ridiculously large magnetic fields'] = True

# don't forget closing! (ends up unreadable otherwise)
dat.close()


### A simple approach to group several data sets (e.g., for a N-d matrix plus 
### the N axes) into a group somewhat autmated (not too many features yet)
dat = h5.HDF5Data(name='data_number_two')
grp = h5.DataGroup('my_data', dat, description='pretty useless',
        taken_by='some student') # arbitrary metadata as kw

# register some data dimensions
grp.add_coordinate('lab temperature', unit='deg C') # arbitrary metadata as kw
grp.add_coordinate('lab air pressure', unit='hPa')
grp.add_value('overnight lab volume increase', unit='l')


# set data (setting requires the dimensions to be set up)
# with this group class we can re-set exisiting arrays; normally hdf5 requires
# deletion and re-creation; like this we can keep the meta data.
grp['lab temperature'] = np.arange(25)
grp['lab air pressure'] = np.arange(25) + 1000
grp['overnight lab volume increase'] = np.random.rand(25,25)

print dat['/my_data/lab temperature']
print dat['/my_data/lab air pressure']
print dat['/my_data/overnight lab volume increase']

dat.close()
