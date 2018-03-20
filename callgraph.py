
from pycallgraph import PyCallGraph
from pycallgraph import Config
from pycallgraph import GlobbingFilter
from pycallgraph.output import GraphvizOutput

from main import main

config = Config()
config.trace_filter = GlobbingFilter(exclude=[
    'pycallgraph.*',
    'requests.*',])

graphviz = GraphvizOutput(output_file='filter_none.png')



with PyCallGraph(output=graphviz, config=config):
    main()
