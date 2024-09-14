import graphviz

class GraphNode:
    def __init__(self, value : int):
        self.value = value
        self.edges : list[GraphEdge] = []

    def add_edge(self, other_node, regex: str):
        self.edges.append(GraphEdge(node_from=self, node_to = other_node, char=regex))

    
class GraphEdge:
    def __init__(self, node_from: GraphNode, node_to: GraphNode, char: str):
        self.node_from = node_from
        self.node_to = node_to
        self.char = char
        self.visited = False
        
    
class GraphBuilder:
    def __init__(self):
        self.reset_graph()
    
    def reset_graph(self):
        self.initial_node = GraphNode(0)
        self.final_node = GraphNode(1)
        self.num_nodes = 2
    
    def main(self,regex : str):
        self.reset_graph()
        self.build_graph(regex, self.initial_node, self.final_node)
        self.graphviz_construct_graph(self.initial_node, self.final_node)
    
    def build_graph(self,lang : str, initial_node : GraphNode, final_node : GraphNode):
        if not lang: 
            if final_node.value == 1:
                initial_node.add_edge(final_node, "&")
            return
        
        if len(lang) == 1:  
            initial_node.add_edge(final_node, lang)
            return
        lang_decomposition = []
        stack = 0
        slice_init = 0
        for i in range(len(lang)):
            if lang[i] == "(":
                stack+=1
                continue
            if lang[i] == ")":
                stack-=1
                continue
            if lang[i] == "+" and stack == 0:
                lang_decomposition.append(lang[slice_init:i])
                lang_decomposition.append(lang[i+1:len(lang)])
                slice_init = i+1
        for langs in lang_decomposition:
            self.build_graph(langs, initial_node, final_node)
        if len(lang_decomposition) > 0: return
        #a partir daqui temos apenas concatenações e linguagens com parenteses () LEMBRANDO QUE TODAS essas linguagens
        #são arestas que ligam o inicio ao fim, ainda não há nó no meio:
        
        #fecho de Kleene:
        if lang[0] == "(":
            #encontrar o fechamento )
            first_closed_parenthesis = 0
            stack = 1
            for i in range(1,len(lang)):
                if lang[i] == "(":
                    stack+=1
                if lang[i] == ")":
                    stack-=1
                    if stack==0:
                        first_closed_parenthesis = i
                        break
            if first_closed_parenthesis+1 < len(lang) and lang[first_closed_parenthesis+1] == "*":
                kleene_node = GraphNode(self.num_nodes)
                self.num_nodes+=1
                initial_node.add_edge(kleene_node,"&")
                self.build_graph(lang[1:first_closed_parenthesis],kleene_node,kleene_node)
                if not lang[first_closed_parenthesis+2:len(lang)]:
                    self.build_graph(lang[first_closed_parenthesis+2:len(lang)],kleene_node,final_node)
                else:
                    intermediate_node = GraphNode(self.num_nodes)
                    self.num_nodes+=1
                    kleene_node.add_edge(intermediate_node,"&")
                    self.build_graph(lang[first_closed_parenthesis+2:len(lang)],intermediate_node,final_node)
            else:
                if not lang[first_closed_parenthesis+1:len(lang)]:
                    self.build_graph(lang[1:first_closed_parenthesis],initial_node,final_node)
                else:
                    intermediate_node = GraphNode(self.num_nodes)
                    self.num_nodes+=1
                    self.build_graph(lang[1:first_closed_parenthesis],initial_node,intermediate_node)
                    self.build_graph(lang[first_closed_parenthesis+1:len(lang)],intermediate_node,final_node)
        #concatenação
        else:
            if lang[1] == "*":
                kleene_node = GraphNode(self.num_nodes)
                self.num_nodes+=1
                kleene_node.add_edge(kleene_node, lang[0])
                initial_node.add_edge(kleene_node,"&")
                if not lang[2:len(lang)]:
                    self.build_graph(lang[2:len(lang)], kleene_node, final_node)
                else:
                    intermediate_node = GraphNode(self.num_nodes)
                    self.num_nodes+=1
                    kleene_node.add_edge(intermediate_node,"&")
                    self.build_graph(lang[2:len(lang)], intermediate_node, final_node)
            else:
                intermediate_node = GraphNode(self.num_nodes)
                self.num_nodes+=1
                initial_node.add_edge(intermediate_node,lang[0])
                self.build_graph(lang[1:len(lang)], intermediate_node, final_node)
        
    def graphviz_construct_graph(self, initial_node : GraphNode, final_node : GraphNode):
        gv = ["digraph automaton{", 
        "rankdir=LR", 
        "node [shape=circle]",
        ]
        gv.append('0 [fillcolor="yellow", style="filled"]')
        gv.append("1 [shape=doublecircle]")
        node_queue : list[GraphNode] = []
        node_queue.append(initial_node)
        while node_queue:
            current_node = node_queue.pop(0)
            for edge in current_node.edges:
                if not edge.visited:
                    gv.append('%s -> %s [label="%s"]' %(edge.node_from.value, edge.node_to.value, edge.char))
                    if edge.node_to and edge.node_to.value != 1 and edge.node_to != edge.node_from:
                        node_queue.append(edge.node_to)
                    edge.visited = True
        gv.append("}")
        graph = "\n".join(gv)
        print(graph)
        dot=graphviz.Source(graph)
        self.graph_dot = dot
        
    def backtracking_through_graph(self, current_node : GraphNode, stack : list[GraphEdge], idx : int, regex : str):
        if not current_node: return
        
        if current_node.value == 1 and idx == len(regex):
            self.possible_paths.append(stack)
            return
        
        for edge in current_node.edges:
            if edge.char == "&":
                #trackear a recursão precisa passar por cópia
                epsilon_stack = stack.copy()
                epsilon_stack.append(edge)
                self.backtracking_through_graph(edge.node_to, epsilon_stack, idx, regex)
            if idx < len(regex) and edge.char == regex[idx]:
                char_transaction_stack = stack.copy()
                char_transaction_stack.append(edge)
                self.backtracking_through_graph(edge.node_to, char_transaction_stack, idx + 1, regex)
        
    
    def compute_state_of_input_chain(self, regex : str):
        self.possible_paths = []
        self.backtracking_through_graph(self.initial_node, [], 0, regex)
        print(f'\nA cadeia {regex} {"" if len(self.possible_paths) else "não"} pertence a linguagem regular dada\n')
        for path in self.possible_paths:
            print("possível caminho:")
            for edge in path:
                print(f'{edge.node_from.value} -> {edge.node_to.value} label = {edge.char}')

Gb = GraphBuilder()
# Gb.main("ab+(b+c)*") 
Gb.main("(a+b)*bb(b+a)*")       
Gb.compute_state_of_input_chain("abb")
#Gb.main("(a(b+c))*") 
