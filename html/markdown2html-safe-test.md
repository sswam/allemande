## Can we embed dangerous HTML in markdown, such as a script tag?

Let's see...

<script>alert("Hello!")</script>

<h1>Hello</h1>

<A href="javascript:alert('Uh oh...')">click me</A>

[Click Me](javascript:alert('Uh oh...'))

![An Image](pix/barbarella.jpg)

![An Image](https://hackersRus.biz/fake-image.cgi)
