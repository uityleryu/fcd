#!/usr/bin/python3.6

# class Product:
#     def __init__(self, index, name, boardid, bomrev, description, cclock, script):
#         self.index = index
#         self.name = name
#         self.boardid = boardid
#         self.bomrev = bomrev
#         self.description = description
#         self.cclock = cclock
#         self.script = script
#         
#     def list(self):
#         print(self.index)
#         print(self.name)
#         print(self.boardid)
#         print(self.bomrev)
#         print(self.description)
#         
#         
# prodlist = []
# prodlist.append(Product("1", "UO", "ea11", "113-00618-01", "UniFi One base", "na", "na"))

# shortname index, name, boardid, bomrev, description, cclock, script
# u1 = {'INDEX': "1", 
#       'NAME': "U1", 
#       'BORADID': "ea11", 
#       'BOMREV': "113-00618-01", 
#       'DESC': "UniFi One base", 
#       'CCLOCK': "na", 
#       'SCRIPT': "na"}

u1 = [0, "U1", "ea11", "113-00618", "UniFi One base", "na", "na"]

prodlist = []
prodlist.append(u1)


def main():
    print(prodlist[0][1])


if __name__ == "__main__":
    main()