import networkx as nx
import matplotlib.pyplot as plt

# Create an empty graph object
G = nx.Graph()

# Add nodes to the graph
G.add_node("Course 1")
G.add_node("Course 2")
G.add_node("Course 3")
G.add_node("Time Slot 1")
G.add_node("Time Slot 2")
G.add_node("Time Slot 3")

# Add edges to the graph
G.add_edge("Course 1", "Time Slot 1")
G.add_edge("Course 2", "Time Slot 2")
G.add_edge("Course 3", "Time Slot 3")
G.add_edge("Course 1", "Time Slot 2")
G.add_edge("Course 2", "Time Slot 3")
G.add_edge("Course 3", "Time Slot 1")

# Define layout for the nodes
pos = nx.spring_layout(G)

# Draw the network diagram
nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1000)
nx.draw_networkx_edges(G, pos, edge_color='gray')
nx.draw_networkx_labels(G, pos)

# Show the diagram
plt.axis('off')
plt.show()