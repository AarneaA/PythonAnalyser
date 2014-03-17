import ast

code = open('test.py').read()
code2 = open('test2.py').read()
parsedCode = ast.parse(code)
parsedCode2 = ast.parse(code2)

print("This is the first code!")
print(ast.dump(parsedCode))
print("=================================")
print("This is the second code!")
print(ast.dump(parsedCode2))
print("=================================")

def simplifyNum(node):
    vars(node).pop('lineno')
    vars(node).pop('col_offset')
    return vars(node)

def simplifyName(node):
    vars(node).pop('lineno')
    vars(node).pop('col_offset')
    vars(node).pop('ctx')
    return vars(node)

def simplifyStr(node):
    vars(node).pop('lineno')
    vars(node).pop('col_offset')
    return vars(node)

def simplifyCall(node):
    simpleCall = {}
    simpleCall['args'] = vars(node).get('args')
    simpleCall['func'] = vars(node).get('func')
    for key, value in simpleCall.items():
        if(key is 'args'):
            simpleCall['args'] = simplifyName(value[0])
        elif(isinstance(value, ast.Name)):
            simpleCall['func'] = simplifyName(value)
    return simpleCall
    
def simplifyList(node):
    simpleNode = []
    for element in vars(node).get('elts'):
        if(isinstance(element, ast.Num)):
           simpleNode.append(simplifyNum(element))
        elif(isinstance(element, ast.Name)):
            simpleNode.append(simplifyName(element))
        elif(isinstance(element, ast.Str)):
            simpleNode.append(simplifyStr(element))
    return simpleNode

def simplifyDict(node):
    print(vars(node))

def simplifyTree(tree):
    resultList = []
    for node in list(ast.iter_child_nodes(tree)):
        simplenode = {}
        vars(node).pop('lineno')
        vars(node).pop('col_offset')
        #print(vars(node))
        for key, value in vars(node).items():
            if(isinstance(value, ast.Num)):
                simplenode[key] = simplifyNum(value)
            elif(isinstance(value, ast.Name)):
                simplifyName(value)
            elif(isinstance(value, ast.Str)):
                simplenode[key] = simplifyStr(value)
            elif(key is 'targets'):
                simplenode[key] = simplifyName(value[0])
            elif(isinstance(value, ast.Call)):
                simplenode[key] = simplifyCall(value)
            elif(isinstance(value, ast.List)):
                simplenode[key] = simplifyList(value)
            elif(isinstance(value, ast.Dict)):
                simplifyDict(value)
            else:
                print(type(value))
        resultList.append(simplenode)
    return resultList

def findMismatches(tree1, tree2):
    found1=[]
    found2=[]
    for index in range(0, len(tree1)):
        #for key, value in tree1[index].items():
            for index2 in range(0, len(tree2)):
                #for key2, value2 in tree2[index2].items():
                    #if(key == key2 and value == value2):
                if(tree1[index] == tree2[index2]):
                    if (index not in found1):
                        found1.append(index)
                    if (index2 not in found2):
                        found2.append(index2)
                    break
    for index in reversed(found1):
        del tree1[index]
    for index in reversed(found2):
        del tree2[index]
    return tree1, tree2
            
        
print("===")
print(findMismatches(simplifyTree(parsedCode), simplifyTree(parsedCode2)))
