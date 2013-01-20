import sys

from flask import Config

class Config(Config):
    """ An object for exposing the settings in app.config.yaml in a nice
    objecty way, and validating some of the contents.
    """
    @property
    def baseforms(self):
        if self._baseforms:
            return self._baseforms

        lang_baseforms = self.opts.get('Baseforms')

        self._baseforms = lang_baseforms
        return self._baseforms

    @property
    def paradigms(self):
        if self._paradigms:
            return self._paradigms

        lang_paradigms = self.opts.get('Paradigms')

        self._paradigms = lang_paradigms
        return self._paradigms
    
    @property
    def reversable_dictionaries(self):
        if self._reversable_dictionaries:
            return self._reversable_dictionaries

        def isReversable(d):
            if d.get('reversable', False):
                return d

        dicts = filter(isReversable, self.opts.get('Dictionaries'))
        language_pairs = {}
        for item in dicts:
            source = item.get('source')
            target = item.get('target')
            path = item.get('path')
            language_pairs[(source, target)] = path

        self._reversable_dictionaries = language_pairs
        return language_pairs

    @property
    def tag_filters(self):
        if not self._tag_filters:
            self._tag_filters = self.opts.get('TagTransforms')
        return self._tag_filters

    @property
    def languages(self):
        if not self._languages:
            self._languages = {}
            for lang in self.opts.get('Languages'):
                self._languages[lang.get('iso')] = lang.get('name')

        return self._languages

    @property
    def dictionaries(self):
        from collections import OrderedDict
        if self._dictionaries:
            return self._dictionaries

        dicts = self.opts.get('Dictionaries')
        language_pairs = OrderedDict()
        for item in dicts:
            source = item.get('source')
            target = item.get('target')
            path = item.get('path')
            language_pairs[(source, target)] = path

        self._dictionaries = language_pairs
        return language_pairs

    @property
    def pair_definitions(self):
        from collections import OrderedDict

        if not self._pair_definitions:
            self._pair_definitions = OrderedDict()
            _par_defs = {}
            for key, path in self.dictionaries.iteritems():
                _from, _to = key
                _from_langs = self.languages[_from]
                _to_langs = self.languages[_to]
                _lang_isos = set(_from_langs.keys()) & set(_to_langs.keys())

                _missing = set(_from_langs.keys()) ^ set(_to_langs.keys())
                if _missing:
                    print >> sys.stderr, "Missing some name translations for"
                    print >> sys.stderr, ', '.join(list(_missing))
                    print >> sys.stderr, "Check Languages in app.config.yaml"
                    sys.exit()

                _names_by_iso = {}
                for iso in _lang_isos:
                    _names_by_iso[iso] = (_from_langs[iso], _to_langs[iso])

                _par_defs[key] = _names_by_iso

            for k, v in self.dictionaries.iteritems():
                self._pair_definitions[k] = _par_defs[k]

        return self._pair_definitions

    @property
    def morphologies(self):
        if self._morphologies:
            return self._morphologies

        self._morphologies = {}

        from morphology import XFST, OBT, Morphology
        formats = {
            'xfst': XFST,
            'obt': OBT,
        }

        for iso, _kwargs_in in self.opts.get('Morphology').iteritems():
            conf_format = _kwargs_in.get('format', False)
            kwargs = {}

            if not conf_format:
                print "No format specified"
                sys.exit()

            m_format = formats.get(conf_format, False)
            if not m_format:
                print "Undefined format"
                sys.exit()

            if 'tool' in _kwargs_in:
                if isinstance(_kwargs_in['tool'], list):
                    _kwt = ''.join(_kwargs_in['tool'])
                else:
                    _kwt = _kwargs_in['tool']
                kwargs['lookup_tool'] = _kwt
            else:
                print "Lookup tool missing"
                sys.exit()

            if 'file' in _kwargs_in:
                if isinstance(_kwargs_in['file'], list):
                    _kwf = ''.join(_kwargs_in['file'])
                else:
                    _kwf = _kwargs_in['file']
                kwargs['fst_file'] = _kwf
            
            if 'inverse_file' in _kwargs_in:
                if isinstance(_kwargs_in['inverse_file'], list):
                    _kwfi = ''.join(_kwargs_in['inverse_file'])
                else:
                    _kwfi = _kwargs_in['inverse_file']
                kwargs['ifst_file'] = _kwfi

            if 'options' in _kwargs_in:
                kwargs['options'] = _kwargs_in['options']

            try:
                self._morphologies[iso] = m_format(**kwargs) >> Morphology(iso)
            except Exception, e:
                print "Error initializing morphology"
                print iso
                print kwargs
                print _kwargs_in

        return self._morphologies

    def test(self, silent=False):
        for item in dir(self):
            if not item.startswith('_') and item != 'test':
                if silent:
                    self.__getattribute__(item)
                else:
                    print item
                    print self.__getattribute__(item)

    def from_yamlfile(self, filename='app.config.yaml'):
        self._languages               = False
        self._pair_definitions        = False
        self._dictionaries            = False
        self._reversable_dictionaries = False
        self._paradigms               = False
        self._baseforms               = False
        self._morphologies            = False
        self._tag_filters             = False

        import yaml
        with open('app.config.yaml', 'r') as F:
            config = yaml.load(F)
        self.opts = config
        self.test(silent=True)
        # Prepare lexica

        from lexicon import Lexicon
        self.lexicon = Lexicon(self)

        return True

# settings = AppConf()

if __name__ == "__main__":
    settings.test(silent=False)

