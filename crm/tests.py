from django.test import TestCase

# Create your tests here.

class test(object):
    def test1(self):
        return 'test'

    a=[test1,]
t=test()
for i in t.a:
    print(type(i))
    print(i(t))