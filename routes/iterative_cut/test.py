# # cutset = []
# # testing = input()
# # if testing != -1:
# #     banned_inputs = list(map(str, testing.split(')(')))
# #     # print(banned_inputs)
# #     print(banned_inputs[1])
# # else:
# #     banned_input = list(map(int, testing))
# # # cutset = banned_inputs
# # # print(cutset)
# i = '(a, a)(b0, b1)(c, c)(d, d)'
# # i = input('Enter a list of tuples: ')
# # citites = ['HCM', 'HN', 'LA', 'NY']
# # sent = "("+citites[0]+","+citites[1]+")"
# # sent = sent + "("+citites[2]+","+citites[3]+")"
# sent = "(HCM,HN)(LA,NY)"

# l = []

# for tup in sent.split(')('):
#     #tup looks like `(a,a` or `b,b`
#     tup = tup.replace(')','').replace('(','')
#     #tup looks like `a,a` or `b,b`
#     l.append(tuple(tup.split(',')))

# print(l)
# a = [[5,4,6],[-6,0,-2]]

# for i in range(len(a[1])):
#     if a[1][i] < 0:
#         a[1][i] = 0

# print(a)
import random
import numpy as np


# a = [3,4,8]
# i = 8
# if i in a:
#     print("yes")
# else:
#     print("no")

# print(np.multiply(a, b))
r = random.uniform(0, 1)
print(r)