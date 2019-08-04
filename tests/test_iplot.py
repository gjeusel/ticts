def test_it_returns_bokeh_figure(smallts):
    fig = smallts.iplot()
    assert fig.title.text == smallts.name
