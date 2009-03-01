from instrument import Instrument
from lib.network import remote_instrument as ri

class Remote_Instrument(Instrument):

    def __init__(self, name, remote_name, host, port=ri.PORT):
        Instrument.__init__(self, name, tags=['remote'])

        self._remote_name = remote_name
        self._client = ri.InstrumentClient(host, port)
        params = self._client.get_instrument_parameters(remote_name)
        for name, info in params.iteritems():
            if info['flags'] & Instrument.FLAG_GET:
                info['get_func'] = self._get
            elif info['flags'] & Instrument.FLAG_SOFTGET:
                info['flags'] ^= (Instrument.FLAG_SOFTGET | Instrument.FLAG_GET)
                info['get_func'] = self._get
            if info['flags'] & Instrument.FLAG_SET:
                info['set_func'] = self._set
            info['channel'] = name
            self.add_parameter(name, **info)

        funcs = self._client.get_instrument_functions(remote_name)
        for name, info in funcs.iteritems():
            setattr(self, name, lambda *args, **kwargs: \
                    self._call(name, *args, **kwargs))
            self.add_function(name, **info)

    def _get(self, channel):
        return self._client.ins_get(self._remote_name, channel)

    def _set(self, val, channel):
        return self._client.ins_set(self._remote_name, channel, val)

    def _call(self, funcname, *args, **kwargs):
        return self._client.ins_call(self._remote_name, funcname, \
                *args, **kwargs)

