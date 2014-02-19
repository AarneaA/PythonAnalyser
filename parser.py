import parser
import ast
import types
import symbol
import token

def findStuff(code):
    ast = parser.suite(code)
    list = ast.tolist()
   # for i in list:
   #     print (i)
    return list

def listify(tree, resultList):
    for child in range(0,len(tree)):
        if type(tree[child]) is list:
            #print("A list")
            #print(tree[child])
            listify(tree[child], resultList)
        else:
            #print("NOT a list")
            #print(tree[child])
            resultList.append(tree[child])
    return resultList

def findStatements(tree, resultList):
    if type(tree) is list:
        for element in tree:
            if type(element) is list:
                if type(element[1]) is list:
                    if element[1][1][0] == 270:
                        resultList.append(element)
            #findStatements(element, resultList)
    return resultList

def filterEqualToken(statementsList, resultList):
    for statement in statementsList:
        treeAsList = []
        listify(statement, treeAsList)
        if 22 in treeAsList:
            resultList.append(treeAsList)
    return resultList

def listAssignments(statementsList, resultList):
    for statement in statementsList:
        singleResult = []
        for element in statement:
            if type(element) is str:
                singleResult.append(element)
        resultList.append(singleResult)
        #print(singleResult)
    return resultList

def printOutAssignments(tree):
    resultList = []
    findStatements(tree, resultList)
    resultList2 = []
    filterEqualToken(resultList, resultList2)
    resultList3 = []
    listAssignments(resultList2, resultList3)
    for assignment in resultList3:
        singleAssignment = ''
        for element in assignment:
            singleAssignment = singleAssignment + element
        print(singleAssignment)

codestring = open('fail.py').read()
tree = findStuff(codestring)
printOutAssignments(tree)
