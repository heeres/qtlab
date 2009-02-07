dmm1 = qt.instruments.create('dmm1', 'example', address='GPIB::1')
dsgen = qt.instruments.create('dsgen', 'dummy_signal_generator')
combined = qt.instruments.create('combined', 'virtual_composite')
combined.add_variable_scaled('magnet', dmm1, 'ch1_output', 0.02, -0.13, units='mT')
#combined.add_variable_combined('waveoffset', [{
#    'instrument': dmm1,
#    'parameter': 'ch2_output',
#    'scale': 1,
#    'offset': 0}, {
#    'instrument': dsgen,
#    'parameter': 'wave',
#    'scale': 0.5,
#    'offset': 0
#    }], format='%.04f')
#arc200 = qt.instruments.create('ARC200', 'Attocube_ARC200', address='ASRL5::INSTR')
#anc150 = qt.instruments.create('ANC150', 'Attocube_ANC150', address='ASRL5::INSTR')
#pm100 = qt.instruments.create('PM100', 'Thorlabs_PM100', address='ASRL5::INSTR')
#atto = qt.instruments.create('atto', 'Attocube_Feedback', anc=1, arc=2)
#xy = qt.instruments.create('XY', 'Dummy_XYStage')
