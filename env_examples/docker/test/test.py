from test_framework import TestSuite

tests = TestSuite({'submission': 'submission.submission'})


@tests.test('test_hello', {'hello': 'submission.hello'})
def test_hello(hello):
    answer = hello()
    if answer is None:  # no answer
        return None
    return 50 if answer == 'Hello' else 0


@tests.test('test_world', {'world': 'submission.world'})
def test_world(world):
    answer = world()
    if answer is None:  # no answer
        return None
    return 50 if answer == 'World' else 0


if __name__ == '__main__':
    tests.run()
