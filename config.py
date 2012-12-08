#!/usr/bin/env python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- vim:fenc=utf-8:et:sw=4:ts=4:sts=4

default_limit = 200
default_sort = 'upload_date'
default_sortorder = 'desc'

institutions = {
    'OMU': 'Oslo Museum',
    'BAR': 'Oslo byarkiv',
    'NF': 'Norsk folkemuseum',
    'ARB': 'Arbeiderbevegelsens arkiv og bibliotek',
    'TELE': 'Telemuseet',
    'NTM': 'Norsk Teknisk Museum',
    'KFS': 'DEXTRA Photo / NTM',
    'UBB': 'Universitetsbiblioteket i Bergen'
    }

columns = [
    ['thumb', 'Miniatyr', True],
    ['filename', 'Filnavn', True],
    ['width', 'Bredde (px)', True],
    ['height', u'Høyde (px)', True],
    ['size', u'Størrelse (kB)', True],
    ['institution', u'Institusjon', True],
    ['imageid', u'Bilde-ID', True],
    ['collection', u'Samling', True],
    ['author', u'Fotograf', True],
    ['date', u'Dato', True],
    ['upload_date', u'Overført', True],
    ['description', u'Beskrivelse', False]
]

fieldnames = ['Bildetittel', 'Motiv', 'Datering', 'Fotograf', 'Avbildet person', 
              'Avbildet sted', 'Utsikt over', 'Utgiver', 'Permalenke',
              'Emneord', 'Bildenummer', 'Historikk', 
              'Permalenke', 'Eierinstitusjon', 'Arkiv/Samling']
