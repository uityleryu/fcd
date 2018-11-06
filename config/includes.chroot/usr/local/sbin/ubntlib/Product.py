#!/usr/bin/python3

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

u1dmp = [0, "U1DMP", "ea13", "113-00618", "UniFi One Dream Machine Plus", "na", "na"]
u1dm = [1, "U1DM", "ea11", "113-00623", "UniFi One Dream Machine", "na", "na"]
u1dmrm = [2, "U1DM-RM", "ea14", "113-00633", "UniFi One Dream Machine RackMount", "na", "na"]
u1dmprm = [3, "U1DMP-RM", "ea15", "113-00631", "UniFi One Dream Machine RackMount", "na", "na"]

prodlist = []
prodlist.append(u1dmp)
prodlist.append(u1dm)
prodlist.append(u1dmrm)
prodlist.append(u1dmprm)

def main():
    print(prodlist[0][1])


if __name__ == "__main__":
    main()
