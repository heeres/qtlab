if qt.config['startdir'] is not None:
    os.chdir(qt.config['startdir'])

if qt.config['startscript'] is not None:
    if os.path.isfile(str(qt.config['startscript'])):
        print 'Executing (user startscript): %s' % qt.config['startscript']
        execfile(qt.config['startscript'])
    else:
        logging.warning('Did not find startscript "%s", skipping' % qt.config['startscript'])

# Add directories containing scripts here. All scripts will be added to the
# global namespace as functions.
qt.scripts.add_directory('examples/scripts')
qt.scripts.scripts_to_namespace(globals())

