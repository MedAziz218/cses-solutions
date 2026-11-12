# Number Spiral — changing the reference point

[Problem statement](statement.md)

My first solution came from looking at the edges of each layer: where does
`max(x, y)²` end up, and how many squares do we need to move to reach the target?
The diagonal formula uses the same idea, but starts from the bend in the layer
instead of an outer endpoint.

## First approach: work inward from an edge

The target belongs to layer `k = max(x, y)`. That layer is an L: its bottom row
and rightmost column. One coordinate is always `k`.

Here is layer `4`, with the inner layers left out. Coordinates are read as
**row `y`, column `x`**:

<table>
<thead><tr><th>y ↓ / x →</th><th>1</th><th>2</th><th>3</th><th>4</th></tr></thead>
<tbody>
<tr><th>1</th><td>·</td><td>·</td><td>·</td><td>10</td></tr>
<tr><th>2</th><td>·</td><td>·</td><td>·</td><td>11</td></tr>
<tr><th>3</th><td>·</td><td>·</td><td>·</td><td>12</td></tr>
<tr><th>4</th><td><b>16 — maximum</b></td><td>15</td><td>14</td><td><b>13 — diagonal</b></td></tr>
</tbody>
</table>

For an even layer, the maximum `k²` is at the bottom-left. For an odd layer,
it is at the top-right. The other endpoint is the first number after the
previous square: `(k − 1)² + 1`.

That gave me four cases: choose the row or column, then use its parity to
subtract from `k²` or add to `(k − 1)²`:

```cpp
if (x >= y && x % 2 == 1) {
    res = x * x - y + 1;
} else if (x >= y && x % 2 == 0) {
    res = (x - 1) * (x - 1) + y;
} else if (y > x && y % 2 == 0) {
    res = y * y - x + 1;
} else {
    res = (y - 1) * (y - 1) + x;
}
```

The equality matters: the diagonal still needs a branch, including when both
coordinates are even.

## A different anchor: the diagonal

Instead of choosing between two endpoints, we can always start at `(k, k)`:
the bend where the layer's row and column meet.

The maximum is `k²`, and the diagonal is `k − 1` steps away from it, so:

```text
D = k² − (k − 1)
  = k² − k + 1
```

For layer `4`, that is `16 − 3 = 13`. To reach `(y = 4, x = 2)`:

```text
Maximum anchor:  16 − 1 = 15
Diagonal anchor: 13 + 2 = 15
```

Same position, different starting point. This led to the version in
[main.cpp](main.cpp):

```cpp
long long k = max(x, y);
long long diagonal = k * k - k + 1;
long long res = diagonal + (k % 2 ? x - y : y - x);
```

## Why does the offset work on both sides?

The key is that **at least one coordinate equals `k`**. From `(k, k)`, reaching
the target means moving along just one arm of the L, not across both dimensions.
So `|x − y|` is exactly the number of steps from the diagonal.

What remains is the direction: do those steps increase or decrease the value?
Parity tells us how the layer is oriented.

| Layer | Target's arm | Offset from the diagonal | Meaning |
| --- | --- | --- | --- |
| Odd | Right column: `x = k` | `x − y = k − y ≥ 0` | Add steps going upward |
| Odd | Bottom row: `y = k` | `x − y = x − k ≤ 0` | Subtract steps going left |
| Even | Right column: `x = k` | `y − x = y − k ≤ 0` | Subtract steps going upward |
| Even | Bottom row: `y = k` | `y − x = k − x ≥ 0` | Add steps going left |

So an odd layer uses `x − y`, and an even layer uses `y − x`. The subtraction
already carries the sign—we do not need another branch to choose between
adding and subtracting.

### A negative offset is intentional

On layer `4`, the diagonal is `13`:

| Target `(y, x)` | Offset `y − x` | Result |
| --- | --- | --- |
| `(1, 4)` | `1 − 4 = −3` | `13 + (−3) = 10` |
| `(4, 4)` | `4 − 4 = 0` | `13 + 0 = 13` |
| `(4, 1)` | `4 − 1 = +3` | `13 + 3 = 16` |

A negative offset does not mean a negative square value. It means the target is
that many steps **before** the diagonal in the layer's numbering.

For an odd layer, the direction reverses. With `k = 5`, the diagonal is `21`:
`(1, 5)` gives `21 + (5 − 1) = 25`, while `(5, 1)` gives
`21 + (1 − 5) = 17`.

This also explains why the coordinates need **signed `long long`**. An unsigned
subtraction can wrap around instead of representing a negative offset.

## Connecting it back to the four cases

For example, when `x = k` and `k` is odd, the original expression becomes:

```text
x² − y + 1
= (x² − x + 1) + (x − y)
= D + (x − y)
```

When `x = k` and `k` is even:

```text
(x − 1)² + y
= (x² − x + 1) + (y − x)
= D + (y − x)
```

The two bottom-row cases reduce to those same offsets. The compact version
is not a different algorithm: it factors out a common reference point and lets
a signed difference express the direction.

Both approaches take **O(1)** time per query and **O(1)** extra space. I kept
only the diagonal version in the code; the four-case version above preserves
the reasoning that got me there.
