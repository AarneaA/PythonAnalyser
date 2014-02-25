import ast

class printAssigns(ast.NodeVisitor):
    def visit_Assign(self, node):
        self.assigns = []
        self.generic_visit(node)
        print(self.assigns)
    def visit_Name(self, node):
        self.assigns.append(node.id)
    def visit_Num(self, node):
        self.assigns.append(node.n)
    def visit_Str(self, node):
        self.assigns.append(node.s)
    def visit_Tuple(self, node):
        self.assigns.append("Tuple:")
        self.generic_visit(node)
    def visit_List(self, node):
        self.assigns.append("List:")
        self.generic_visit(node)
    def visit_Set(self,node):
        self.assigns.append("Set:")
        self.generic_visit(node)

code = open('fail.py').read()

parsedCode = ast.parse(code)
printAssigns().visit(parsedCode)
