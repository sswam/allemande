The quadratic equation, where $a \ne 0$:

$$
ax^2 + bx + c = 0 
$$

has solutions given by the formula:

$$
x = {-b \pm \sqrt{b^2-4ac} \over 2a}
$$

To understand this formula, consider the following simple equation:

$$
(x - B)^2 = C 
$$

This can readily be solved:

$$
x = B \pm \sqrt{C} 
$$

That simple equation has geometrically meaningful parameters, and can be expanded:

$$
x^2 - 2Bx + B^2 - C = 0 
$$

We can multiply by $a$ to add a coefficient on the quadratic term:

$$
ax^2 - 2aBx + a(B^2 - C) = 0 
$$

This is equivalent to a general quadratic equation:

$$
ax^2 + bx + c = 0 
$$

Where:

$$
b = -2aB 
$$

$$
c = a(B^2 - C) 
$$

Writing $B$ and $C$ in terms of $a$, $b$ and $c$:

$$
B = -\frac{b}{2a} 
$$

$$
C = \left(\frac{b}{2a}\right)^2 - \frac{c}{a} 
$$

Substitute into the first solution to derive the conventional quadratic formula:

$$
x = B \pm \sqrt{C} 
$$
	
$$
x = -\frac{b}{2a} \pm \sqrt{ \left(\frac{b}{2a}\right)^2 - \frac{c}{a} } 
$$
	
$$
x = -\frac{b}{2a} \pm \sqrt{ \frac{b^2}{4a^2} - \frac{4ac}{4a^2} } 
$$
	
$$
x = -\frac{b}{2a} \pm \frac{ \sqrt{ b^2 - 4ac } }{2a} 
$$
	
$$
x = {-b \pm \sqrt{ b^2 - 4ac } \over 2a} 
$$

I like this derivation, because we solve the simplified quadratic equation $(x - B)^2 = C$ in a single step.
