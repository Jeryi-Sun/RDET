#!/usr/bin/python3.6
# encoding:utf-8
import math, ipaddress
from copy import deepcopy
import random

# import pdb
# import ptvsd
# ptvsd.enable_attach(('219.243.212.103',3000))
# ptvsd.wait_for_attach()

"""
从文件中读取IPv6地址，并将IPv6地址转换为有序的向量序列
"""


class AddrVecList(list):
    """
    地址向量列表，继承自内置list类型，
    为排序时便于比较，对>=和<=运算符重载
    """

    def __init__(self):
        list.__init__([])

    # 重载>=运算符
    def __ge__(self, value):
        ge = True
        for i in range(len(self)):
            if self[i] < value[i]:
                ge = False
                break
        return ge

    # 重载<=运算符
    def __le__(self, value):
        le = True
        for i in range(len(self)):
            if self[i] > value[i]:
                le = False
                break
        return le


# def InputAddrs(input='files/source.hex', beta=16):
def InputAddrs(input='data.csv', delta=16):
    """
    从输入文件中读取IPv6地址列表，并转换为有序的地址向量序列

    Args：
        input：存储了所有种子地址的文件（.hex:不带冒号；.txt：带冒号，可压缩）
        delta:地址向量每一维度的基数

    Return:
        V：有序的地址向量序列
    """
    print("Hello!")
    IPv6 = []
    count = 0
    for line in open(input):
        if line != '':
            IPv6.append(line)
            count += 1
    IPv6 = [addr.strip('\n') for addr in IPv6]
    IPv6 = random.sample(IPv6, 1000000)
    print("random sample")
    if input[-3:] == 'txt':
        # 将所有IPv6地址全部转换为未压缩形式
        for i in range(len(IPv6)):
            IPv6[i] = ipaddress.IPv6Address(IPv6[i])
            IPv6[i] = IPv6[i].exploded
            IPv6[i] = IPv6[i].replace(':', '')

    V = AddrsToSeq(IPv6, math.log(delta, 2))
    return V


def AddrsToSeq(addr=[], m=4, lamda=128):
    """
    将标准IPv6地址列表转换为有序的向量列表

    Args：
        addr：标准化的IPv6地址列表，列表的每个元素为IPv6地址的无冒号16进制写法
        m：地址向量的每一维度代表的二进制数长度
        lamda：IPv6地址总长度（默认为128）

    Returns：
        转换得到的IPv6地址向量二维列表，
        每个一维列表中的每个元素代表一个IPv6地址向量的在一个维度上的十进制值
    """

    if lamda % m != 0:
        print('!!EXCEPTION: lamda % m != 0')
        exit()
    V = AddrVecList()
    # V = []  #地址向量列表
    # N = []  #地址对应的整数列表，便于排序
    for i in range(len(addr)):
        if addr[i] == '':
            break
        # addr_hex = addr[i].replace(':','')
        N = int(addr[i], 16)  # 将IPv6地址（字符串）转换为对应的整数值
        v = []  # 每个地址向量的值（整数列表）
        for delta in range(1, int(lamda / m + 1)):
            x1 = int(2 ** (m * (lamda / m - delta)))  # 注意需显式地将结果转换为整数
            x2 = N % int(x1 * (2 ** m))
            x3 = N % x1
            v.append(int((x2 - x3) / x1))
        V.append(v)
    V = sorted(V)
    return V


def SeqToAddrs(node, number, args):
    """

    将地址向量列表生成指定数目的IPv6地址

    Args：
        node：生成地址的节点
        number：在本区域中需要生成的数目
        args： 参数列表

    Return：
        addr_list：IPv6地址列表
    """

    # 先看看空间大小够不够 不够的话进行扩展
    changed = False  # 用于记录空间是否扩展
    # 当已经搜索的空间加上待搜索的空间大于当前空间时就从DS中弹出一个维度，扩充搜索空间
    while number + len(node.SS) > node.region_size and node.DS.stack != node.parent.DS.stack:  # todo 修改归并节点
        delta = node.DS.pop()
        if node.DS.stack == node.parent.DS.stack:
            break
        node.ExpandTS(delta)
        node.searched_dim += 1
        node.region_size = pow(args.delta, node.searched_dim) * len(node.TS)  # 新的搜索空间

        # todo 判断是否合并节点 剔除已经归并的节点
        changed = True

    #  如果地址空间发生了扩充那么就重新生成地址空间
    addr_list = []
    if changed or node.generated_address==None:
        seq = node.TS
        if seq==[]:
            return set()

        m = int(128 / len(seq[0]))  # 地址向量的每一维度代表的二进制数长度
        seq = deepcopy(seq)
        value = 0  # 地址对应的整数值
        a_vec = seq[0]  # 一个地址向量，用于判断哪个维度被Expand过
        # (列表中所有向量被Expand的维度都是相同的)
        vec_dim = len(a_vec)  # 地址向量的维数

        for i in range(vec_dim):
            if a_vec[i] == -1:  # i维度被Expand，需要在列表中增加地址
                seq = SeqExpand(seq, i, m)

        for vector in seq:
            for v_i in vector:
                value = value * (2 ** m) + v_i
            addr = ipaddress.IPv6Address(value)
            addr_list.append(str(addr))
            value = 0
    # 如果地址空间发生了改变或者node本身记录的搜索空间为空
    if changed or node.generated_address==None:
        node.generated_address = addr_list

    # 当前地址集合减去之前已经生成过的地址集合，之后从中选取指定数目的地址数
    rest_addr = list(set(node.generated_address) - node.SS)


    if len(rest_addr)<number:
        node.flag_child = number-len(rest_addr)
        addr_result = random.sample(rest_addr, len(rest_addr))
    else:
        addr_result = random.sample(rest_addr, number)
    return addr_result


def get_rawIP(IP):
    # 标准IP -> hex IP
    seglist = IP.split(':')
    if seglist[0] == '':
        seglist.pop(0)
    if seglist[-1] == '':
        seglist.pop()
    sup = 8 - len(seglist)
    if '' in seglist:
        sup += 1
    ret = []
    for i in seglist:
        if i == '':
            for j in range(0, sup):
                ret.append('0' * 4)
        else:
            ret.append('{:0>4}'.format(i))
    rawIP = ''.join(ret)
    assert (len(rawIP) == 32)
    return rawIP


def SeqExpand(seq, idx, m=4):
    """
    将列表seq中所有向量的idx维度上的-1还原为1-2^m区间内的所有数

    Args：
        seq：待还原的地址向量列表
        idx：待还原的维度（从0开始）
        m:地址向量的每一维度代表的二进制数长度

    Return:
        new_seq：更新后的地址向量列表
    """

    new_seq = []
    for vector in seq:
        for v in range(2 ** m):
            vector[idx] = v
            new_seq.append(deepcopy(vector))

    return new_seq


# def SortVecList(V):
#     """
#     对地址向量列表进行快速排序

#     Args:
#         未排序的地址向量列表
#     """

#     QuickSort(V, 0, len(V) - 1)

# def QuickSort(V, low, high):
#     """
#     对V[low]和V[high]之间的元素进行快速排序

#     Args：
#         V：待排序的向量列表
#         low：待排序的元素下标下界
#         high：待排序的元素下标上界
#     """

#     if low < high:
#         pivotloc = Partition(V, low, high)
#         QuickSort(V, low, pivotloc - 1)
#         QuickSort(V, pivotloc + 1, high)

# def Partition(V, low, high):
#     """
#     以V[low]做枢轴，将V[low]和V[high]之间的元素做划分

#     Args:
#         V：待排序的向量列表
#         low：待排序的元素下标下界
#         high：待排序的元素下标上界

#     Return:
#         枢轴元素的下标
#     """    
#     pivot_v = V[low]
#     while low < high:
#         while low < high and V[high] >= pivot_v:
#             high -= 1
#         V[low] = V[high]
#         while low < high and V[low] <= pivot_v:
#             low += 1
#         V[high] = V[low]
#     V[low] = pivot_v
#     return low


if __name__ == '__main__':
    # IPv6 = ["2c0f:ffd8:0030:ac1d:0000:0000:0000:0146","2001:0000:0000:0000:0000:0000:1f0d:4004"]
    # for i in range(len(IPv6)):
    #     IPv6[i]=IPv6[i].replace(":","")
    # V = AddrsToSeq(IPv6)
    # print(SeqToAddrs(V))
    # # pdb.set_trace()

    # V = InputAddrs()
    # if V == None:
    #     print("V is none!")
    # else:
    #     for v in V:
    #         print(v)
    InputAddrs("data.csv")
