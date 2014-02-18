import betterconfig


def test_literals():
    expected = {'config': {
        'foo': 1,
        'bar': ['a', 'list', 'of', 'strings'],
        'baz': "just a plain old string"}}
    actual = betterconfig.load('examples/literals.cfg')
    assert expected == actual
