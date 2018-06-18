import os

from flat import rgb, font, shape, strike, document


def test_tutorial(tmpdir):
    red = rgb(255, 0, 0)
    dejavu = font.open("DejaVuSans.subset.otf")
    figure = shape().stroke(red).width(2.5)
    headline = strike(dejavu).color(red).size(20, 24)

    d = document(100, 100, "mm")
    p = d.addpage()
    p.place(figure.circle(50, 50, 20))
    p.place(headline.text("Hello world!")).frame(10, 10, 80, 80)

    png_file = str(tmpdir.join("hello.png"))
    svg_file = str(tmpdir.join("hello.svg"))
    pdf_file = str(tmpdir.join("hello.pdf"))
    p.image(kind="rgb").png(png_file)
    p.svg(svg_file)
    d.pdf(pdf_file)
    assert os.path.exists(png_file)
    assert os.path.exists(svg_file)
    assert os.path.exists(pdf_file)
