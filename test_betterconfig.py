import betterconfig


def test_literals():
    expected = {'config': {
        'foo': 1,
        'bar': ['a', 'list', 'of', 'strings'],
        'baz': "just a plain old string"}}
    actual = betterconfig.load('examples/literals.cfg')
    assert expected == actual


def test_top_level():
    expected = {
        'foo': {'numbers': [4, 8, 12]},
        'config': {
            'bar': 24
        }
    }
    actual = betterconfig.load('examples/top_level.cfg')
    assert expected == actual
