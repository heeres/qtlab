from instrument import Instrument
from lib.network import remote_instrument as ri
import logging

class Remote_Instrument(Instrument):

    def __init__(self, name, remote_name, inssrv):
        Instrument.__init__(self, name, tags=['remote'])

        self._remote_name = remote_name
        self._srv = inssrv
        params = self._srv.get_ins_parameters(remote_name)
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

        funcs = self._srv.get_ins_functions(remote_name)
        for name, info in funcs.iteritems():
            try:
                func = self.create_lambda(name, info.get('argspec', None))
                if 'doc' in info:
                    func.__doc__ = info['doc']
                setattr(self, name, func)
                self.add_function(name, **info)
            except Exception, e:
                logging.warning('Failed to create function %s: %s', name, e)

    def create_lambda(self, funcname, argspec=None):
        if argspec is None:
            codestr = 'lambda *args, **kwargs: self._call("%s", *args, **kwargs)' % funcname
        else:
            if len(argspec[0]) < 1:
                return None
            args = ','.join(argspec[0][1:])
            if argspec[1] is not None:
                args = ','.join((args, '*%s' % argspec[1]))
            if argspec[2] is not None:
                args = ','.join((args, '**%s' % argspec[2]))

            codestr = 'lambda %s: self._call("%s"' % (args, funcname)
            if args != '':
                codestr += ', %s' % args
            codestr += ')'

        return eval(codestr, {'self': self})

    def _get(self, channel):
        return self._srv.ins_get(self._remote_name, channel)

    def _set(self, val, channel):
        return self._srv.ins_set(self._remote_name, channel, val)

    def _call(self, funcname, *args, **kwargs):
        return self._srv.ins_call(self._remote_name, funcname, *args, **kwargs)

def detect_instruments():
    remote_instrument.create_all()

