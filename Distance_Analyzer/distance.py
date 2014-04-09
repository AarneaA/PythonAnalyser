import ast

import time

a = time.time()

code = open('test.py').read()
code2 = open('test2.py').read()
parsedCode = ast.parse(code)
parsedCode2 = ast.parse(code2)

print("This is the first tree dump!")
print(ast.dump(parsedCode, False, False))
print("=================================")
print("This is the second tree dump!")
print(ast.dump(parsedCode2, False, False))
print("=================================")

b = time.time()

print("Time to parse and dump : " + str(b-a))

#"""recurseAST returns AST object as a dict for simpler viewing"""
#TODO:DONE Fix issue where ast objects don't get simplified in lists
def recurseAST(astObject):
    simpleNode = {}
    for key, value in vars(astObject).items():
        if(isinstance(value, ast.AST)):
            simpleNode[key] = recurseAST(value)
        elif(isinstance(value, list)):
            simpleList = []
            for listValue in value:
                simpleList.append(recurseAST(listValue))
            simpleNode[key] = simpleList
        else:
            simpleNode[key] = value
    return simpleNode

#"""SimpleTreeList returns an abstract syntax tree as a list of its nodes as dicts
#    so its nodes could be matched with a different tree's"""
#"""could and maybe should be deleted and matchNodes function reworked to include some of its
#    functionality for less memory and processor use (no big gain on speed)"""
def simpleTreeList(tree):
    a = time.time()
    resultList = []
    for node in list(ast.iter_child_nodes(tree)):
        simpleNode = {}
        #print(vars(node))
        for key, value in vars(node).items():
            if (isinstance(value, ast.AST)):
                simpleNode[key] = recurseAST(value)
            elif (isinstance(value, list)):
                simpleList = []
                for listValue in value:
                    if (isinstance(listValue, ast.AST)):
                        simpleList.append(recurseAST(listValue))
                simpleNode[key] = simpleList
        resultList.append(simpleNode)
    b = time.time()
    print("SimpleTreeList time : " +str(b-a))
    return resultList

#"""Levenshtein returns levenshtein distance between two strings. Used to assess distance between nodes for matching"""
#"""Not used to assess distances between trees, due to it being too complex and hard to match nodes that way"""
#This is the old levenshtein, which is 3x slower than the new one.
def levenshteinOld(string1,  string2):
    a = time.time()
    distances = {}
    string1 = ' ' + string1
    string2 = ' ' + string2
    length1 = len(string1)
    length2 = len(string2)
    for i in range(length1):
        distances[i, 0] = i
    for j in range(length2):
        distances[0 , j] = j
    for j in range(1, length2):
        for i in range(1, length1):
            if(string1[i] == string2[j]):
                distances[i, j] = distances[i-1, j-1]
            else:
                distances[i, j] = min(distances[i-1, j] +1, distances[i, j-1] +1, distances[i-1, j-1] + 1)
    b = time.time()
    print("Levenshtein time : " + str(b-a))
    return distances[length1-1, length2-1]

#Faster levenshtein taken from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
 
    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)
 
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]


#"""TODO: UNNECESSARY the for cycles on second nodes can be removed and replaced with attempts of finding key-value pairs by the keys of the first node
#from the single for-cycle... Probably unnecessary, because the gain would be small (< 0.0001) and in some cases I need both cycles anyway"""
def matchNodes(treeList1, treeList2):
    a = time.time()
#    """ TODO:DONE add checks for lengths between node item lists, for faster work and to avoid matching nodes with ridicullously high edit distances (written and erased nodes)"""
    resultList = []
#    """ First match all the nodes that weren't changed (ignoring lineno and col_offset values)"""
    for node in treeList1:
        for node2 in treeList2:
            if(len(node) == len(node2)):
                aMatch = True
                for key1, value1 in node.items():
                    for key2, value2 in node2.items():
                        if(key1 == key2):
                            if(len(value1) != len(value2)):
                                aMatch = False
                            elif(isinstance(value1, list) and isinstance(value2, list)):
                                for element in value1:
                                    for element2 in value2:
                                        for valueKey, valueValue in element.items():
                                            if(valueKey != 'lineno' and valueKey != 'col_offset'):
                                                for valueKey2, valueValue2 in element2.items():
                                                    if(valueKey2 != 'lineno' and valueKey != 'col_offset'):
                                                        if(valueKey == valueKey2 and valueValue != valueValue2):
                                                            aMatch = False
                            else:
                                for valueKey, valueValue in value1.items():
                                    if(valueKey != 'lineno' and valueKey != 'col_offset'):
                                        for valueKey2, valueValue2 in value2.items():
                                            if(valueKey2 != 'lineno' and valueKey != 'col_offset'):
                                                if(valueKey == valueKey2 and valueValue != valueValue2):
                                                    aMatch = False
                if(aMatch):
                    resultList.append([node, node2])
                    treeList1.remove(node)
                    treeList2.remove(node2)
                    break
    b = time.time()
    print("Time to match unchanged : " + str(b-a))
#    """ Now to continue with the leftover nodes, that weren't unchanged, and find matches between them"""
#    """Matching nodes with unchanged variable names"""
    a = time.time()
    for node in treeList1:
        for node2 in treeList2:
            aMatch = False
            for key, value in node.items():
                for key2, value2 in node2.items():
                        #if(key2 == 'targets'):
#                    """ For a single case, where one variable has a value and the other doesn't I have to check
#                        whether i am comparing a list with a list, a list with a dict, a dict with a list or a dict with a dict
#                        might need to figure out a /prettier/ way"""
                    if(isinstance(value, list)):
                        for element in value:
                            if(isinstance(value2, list)):
                                for element2 in value2:
                                    for valueKey, valueValue in element.items():
                                        if(valueKey == 'id'):
                                            for valueKey2, valueValue2 in element2.items():
                                                if(valueKey2 =='id'):
                                                    if(valueValue == valueValue2):
                                                        aMatch = True
                            else:
                                for valueKey, valueValue in element.items():
                                    if(valueKey == 'id'):
                                        for valueKey2, valueValue2 in value2.items():
                                            if(valueKey2 =='id'):
                                                if(valueValue == valueValue2):
                                                    aMatch = True
                    else:
                        if(isinstance(value2, list)):
                            for element2 in value2:
                                for valueKey, valueValue in value.items():
                                    if(valueKey == 'id'):
                                        for valueKey2, valueValue2 in element2.items():
                                            if(valueKey2 =='id'):
                                                if(valueValue == valueValue2):
                                                    aMatch = True
                        else:
                            for valueKey, valueValue in value.items():
                                if(valueKey == 'id'):
                                    for valueKey2, valueValue2 in value2.items():
                                        if(valueKey2 =='id'):
                                            if(valueValue == valueValue2):
                                                aMatch = True
                                
            if(aMatch):
                resultList.append([node, node2])
                treeList1.remove(node)
                treeList2.remove(node2)
    b = time.time()
    print("Time to match same variables : " + str(b-a))
#    """Matches nodes with minimal edit distance between them lineno and col_offset add 1 to distance per difference, other values add levenshtein distance"""
    a = time.time()
    distances={}
    for i in range(len(treeList1)):
        for j in range(len(treeList2)):
            distances[i, j] = -1
    for nodePair, value in distances.items():
        if(len(treeList1[nodePair[0]]) == len(treeList2[nodePair[1]])):
            for key1, value1 in treeList1[nodePair[0]].items():
                for key2, value2 in treeList2[nodePair[1]].items():
                    if(key1 == key2):
                        if(isinstance(value1, list) and isinstance(value2, list)):
                                for element in value1:
                                    for element2 in value2:
                                        for valueKey, valueValue in element.items():
                                            for valueKey2, valueValue2 in element2.items():
                                                if(valueKey == valueKey2):
                                                    if(valueKey == 'lineno' or valueKey == 'col_offset'):
                                                        if(distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] == -1):
                                                            distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + abs(valueValue - valueValue2) + 1
                                                        else:
                                                            distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + abs(valueValue - valueValue2)
                                                    else:
                                                        if(distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] == -1):
                                                            distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + levenshtein(str(valueValue), str(valueValue2)) + 1
                                                        else:
                                                            distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + levenshtein(str(valueValue), str(valueValue2))
                        else:
                            for valueKey, valueValue in value1.items():
                                for valueKey2, valueValue2 in value2.items():
                                    if(valueKey == valueKey2):
                                        if(valueKey == 'lineno' or valueKey == 'col_offset'):
                                            if(distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] == -1):
                                                distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + abs(valueValue - valueValue2) + 1
                                            else:
                                                distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + abs(valueValue - valueValue2)
                                        else:
                                            if(distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] == -1):
                                                distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + levenshtein(str(valueValue), str(valueValue2)) + 1
                                            else:
                                                distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] = distances[treeList1.index(treeList1[nodePair[0]]), treeList2.index(treeList2[nodePair[1]])] + levenshtein(str(valueValue), str(valueValue2))
                            for valueKey, valueValue in value1.items():
                                #TODO:DONE add distance per key1 missing in treeList2
                                if(valueKey not in value2):
                                    distances[nodePair[0], nodePair[1]] += 1
                            for valueKey, valueValue in value2.items():
                                 #TODO:DONE add distance per key2 missing in treeList1
                                if(valueKey not in value1):
                                    distances[nodePair[0], nodePair[1]] += 1
    newDistances = {}
    for key, value in distances.items():
        if (value != -1):
            newDistances[key] = value
    del distances
    addedFromFirst = []
    addedFromSecond = []
    newDistTuple = sorted(newDistances.items(), key=lambda x:x[1])
    print(newDistTuple)
    for pair in newDistTuple:
        if(pair[0][0] not in addedFromFirst and pair[0][1] not in addedFromSecond):
            addedFromFirst.append(pair[0][0])
            addedFromSecond.append(pair[0][1])
    for index in range(len(addedFromFirst)):
        resultList.append([treeList1[addedFromFirst[index]], treeList2[addedFromSecond[index]]])
    for index in sorted(addedFromFirst, reverse = True):
        del treeList1[index]
    for index in sorted(addedFromSecond, reverse = True):
        del treeList2[index]
    b = time.time()
    print("Time to match by smallest distances : " + str(b-a))
    for node in treeList1:
        resultList.append([node, None])
    for node in treeList2:
        resultList.append([None, node])
    return resultList

#"""TODO: function to detect differences between two nodes, matched by the matchNodes function"""
#"""TODO: replace the current prints with returning a dict"""
#"""TODO: DONE fix issue where sometimes big dicts in lists are being compared"""
def nodeDiff(node1, node2):
    resultDict = {}
    if(node1 == None):
        resultDict['Added node'] = node2
        #print("Added node")
    elif(node2 == None):
        resultDict['Deleted node'] = node1
        #print("Deleted node")
    else:
        for key, value in node1.items():
            for key2, value2 in node2.items():
                if(key == key2):
                    if(isinstance(value, list) and isinstance(value2, list)):
                        resultList = []
                        for element in value:
                            for element2 in value2:
                                for valueKey, valueValue in element.items():
                                    for valueKey2, valueValue2 in element2.items():
                                        if(valueKey == valueKey2):
                                            if(valueValue != valueValue2):
                                                resultList.append({valueKey : (valueValue, valueValue2)})
                                                print("diff  : "+ str(valueValue) + " and " + str(valueValue2))
                                            else:
                                                #pass
                                                print("equal : "+ str(valueValue) + " and " + str(valueValue2))
                        if(len(resultList)>0):
                            resultDict[key] = resultList
                    else:
                        for valueKey, valueValue in value.items():
                            for valueKey2, valueValue2 in value2.items():
                                if (isinstance(valueValue, list) and isinstance(valueValue2, list)):
                                    resultList = []
#Get indexes over the range of the shorter list, then a separate cycle will get indexes of len difference over longer list
                                    for index in range(min(len(valueValue), len(valueValue2))):
                                        for listKey, listValue in valueValue[index].items():
                                            for listKey2, listValue2 in valueValue2[index].items():
                                                if(listKey == listKey2):
                                                    if(listValue != listValue2):
                                                        resultList.append({listKey : (listValue, listValue2)})
                                                        print("diff  : "+ str(listValue) + " and " + str(listValue2))
                                                    else:
                                                        print("equal : "+ str(listValue) + " and " + str(listValue2))
                                    for index in range(max(len(valueValue), len(valueValue2)) - min(len(valueValue), len(valueValue2))):
                                        if(len(valueValue)<len(valueValue2)):
                                            longerList = valueValue2
                                        else:
                                            longerList = valueValue
                                        for listKey, listValue in longerList[index].items():
                                            if(len(valueValue)<len(valueValue2)):
                                                resultList.append({listKey : (None, ListValue)})
                                            else:
                                                resultList.append({listKey : (ListValue, None)})
                                            print("diff  : "+ str(listValue))
                                    resultDict[key] = resultList
                                else:
                                    if(valueKey == valueKey2):
                                        if(valueValue != valueValue2):
                                            print("diff  : "+ str(valueValue) + " and " + str(valueValue2))
                                            resultDict[valueKey]= (valueValue, valueValue2)
                                        else:
                                            print("equal : "+ str(valueValue) + " and " + str(valueValue2))
    return resultDict

#"""TODO: A function that processes multiple sets of nodeDiff outputs and returns joined diffs
#       for example multiple changes on same variable multiple lineno increments over multiple nodes"""

a = time.time()
for thing in (matchNodes(simpleTreeList(parsedCode),simpleTreeList(parsedCode2))):
    for node in thing:
        print(node)
        print("")
    print(nodeDiff(thing[0], thing[1]))
    print("\n\n")
b = time.time()
print ("Time for analysis and print-out : " + str(b-a))
