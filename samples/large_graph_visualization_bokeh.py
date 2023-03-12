from bokeh.io import show, output_file
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool
from bokeh.plotting import from_networkx
import networkx as nx


G = nx.gnm_random_graph(500, 1000)

plot = Plot(title="Large Graph Visualization with Bokeh", x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))

graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))

graph_renderer.node_renderer.glyph = Circle(size=5, fill_color='blue')
graph_renderer.edge_renderer.glyph = MultiLine(line_color='gray', line_alpha=0.8, line_width=0.2)
plot.renderers.append(graph_renderer)

hover = HoverTool(tooltips=[('index', '@index')])
plot.add_tools(hover)

output_file("large_graph.html")
show(plot)