def test_linearizer_traverses_graph_fast_enough(benchmark, dense_graph, linearizer):
    benchmark(linearizer.linearize, dense_graph)
