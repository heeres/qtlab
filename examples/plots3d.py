import numpy as np

x = np.linspace(-2 * np.pi, 2 * np.pi, 200)
y = np.linspace(-2 * np.pi, 2 * np.pi, 200)
X, Y = meshgrid(x, y)
Z = np.sinc(np.sqrt(X**2 + Y**2))

# Plot in 3D
plot3(ravel(X), ravel(Y), ravel(Z),
        style='3d',
        palette='jet',
        gamma=1.25,
        title='Example 3D plot',
        name='example_3d',
        clear=True)

# Plot as image (only for complete NxM data sets!)
p = plot3(ravel(X), ravel(Y), ravel(Z),
        style='image',
        palette='hot',
        title='Example image',
        name='example_img',
        xrange=(-2 * np.pi, 2 * np.pi),
        yrange=(-2 * np.pi, 2 * np.pi),
        clear=True)

