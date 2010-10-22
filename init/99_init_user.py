if qt.config['startdir'] is not None:
    os.chdir(qt.config['startdir'])

if qt.config['startscript'] is not None:
    if os.path.isfile(str(qt.config['startscript'])):
        print 'Executing (user startscript): %s' % qt.config['startscript']
        execfile(qt.config['startscript'])
    else:
        logging.warning('Did not find startscript "%s", skipping' % qt.config['startscript'])

# Add script directories. Read index and put in namespace
if qt.config['scriptdirs'] is not None:
    for dirname in qt.config['scriptdirs']:
        qt.scripts.add_directory(dirname)
    qt.scripts.scripts_to_namespace(globals())

