# Two Knights ,  how I worked it out

[Problem statement](statement.md)

The task is to count ways to put two knights on an `i × i` board without them
attacking each other, for every board size from `1` to `n`.

Instead of counting the valid placements directly, I started with **every pair
of squares** and subtracted the pairs where the knights attack:

```text
squares = i*i
all pairs = squares × (squares − 1) / 2
answer = all pairs − attacking pairs
```

We use combinations because swapping the knights does not create a new placement.
The interesting part was figuring out how to count the attacking pairs.

## My first approach: go row by row

I pictured a knight at each position in a row and counted what it could attack
**in the lower rows only**. That way, each pair is counted once, not again
from the other knight's position.

That leaves three parts of the board:

- The first `i − 2` rows have both kinds of downward move available.
- Row `i − 1` is special: only a move one row down is possible.
- Row `i` has nothing below it, so it contributes nothing.

### Working through a 6 × 6 board

Each of the first four rows contributes:

- **One row down, two columns sideways:** there are `6 − 2 = 4` three-column
  spans, with two attack directions each. That gives **8 pairs**.
- **Two rows down, one column sideways:** there are `6 − 1 = 5` adjacent-column
  pairs, again with two directions each. That gives **10 pairs**.

So each of those rows contributes `8 + 10 = 18` attacking pairs. The fifth row
only contributes the first kind of move: `8` pairs. The sixth contributes none.

<table>
<thead>
<tr><th>Row</th><th colspan="6">6 × 6 board</th><th>Attacking pairs</th><th>Contribution</th></tr>
</thead>
<tbody>
<tr><th>1</th><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td><b>18</b> = 8 + 10</td><td rowspan="4"><b>x = 4 × 18 = 72</b><br>First i − 2 rows</td></tr>
<tr><th>2</th><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td><b>18</b> = 8 + 10</td></tr>
<tr><th>3</th><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td><b>18</b> = 8 + 10</td></tr>
<tr><th>4</th><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td>🟦</td><td><b>18</b> = 8 + 10</td></tr>
<tr><th>5</th><td>🟧</td><td>🟧</td><td>🟧</td><td>🟧</td><td>🟧</td><td>🟧</td><td><b>8</b> = 2(6 − 2)</td><td><b>y = 8</b><br>Penultimate row</td></tr>
<tr><th>6</th><td>⬜</td><td>⬜</td><td>⬜</td><td>⬜</td><td>⬜</td><td>⬜</td><td><b>0</b> ,  no lower rows</td><td>Not included</td></tr>
</tbody>
<tfoot><tr><td colspan="9" align="center"><b>Attacking pairs = x + y = 72 + 8 = 80</b></td></tr></tfoot>
</table>

I called the contribution of the first `i − 2` rows **`x`**, and the contribution
of the penultimate row **`y`**. My original expressions were:

```cpp
x = (10 + 4 * (i - 4)) * (i - 2);
y = 4 + 2 * (i - 4);
```

Those constants make sense starting from a `4 × 4` board: a normal row
contributes `10` pairs and the penultimate row contributes `4`. Each extra
column adds four pairs to a normal row, two of each move shape, and two pairs
to the penultimate row.

For `i = 6`, that becomes:

```text
x = (10 + 4 × 2) × 4 = 72
y = 4 + 2 × 2        =  8
attacking pairs     = 80

all pairs = 36 × 35 / 2 = 630
answer    = 630 − 80    = 550
```

`countByRows()` keeps this approach. For `i < 3`, all pairs are valid because
no knight attack fits on the board.

## Simplifying the count

The two expressions look different, but there is a common factor:

```text
x = (4i − 6)(i − 2)
y = 2(i − 2)

x + y = (i − 2)[(4i − 6) + 2]
      = (i − 2)(4i − 4)
      = 4(i − 1)(i − 2)
```

The formula is shorter now, but I wanted to understand what it meant on the
board, not just why the algebra worked.

## The rectangle interpretation

A knight attack always spans either **two rows and three columns**, or **three
rows and two columns**. In each of those rectangles, there are exactly two
attacking pairs.

Matching letters and colors show a pair: **A ↔ A** or **B ↔ B**.
These are two possible pairs, not four knights placed together.

<table>
<thead><tr><th>2 rows × 3 columns</th><th>3 rows × 2 columns</th></tr></thead>
<tbody><tr><td valign="top" align="center">
<table aria-label="Two rows and three columns">
<tbody>
<tr><td align="center">🔵 <b>A</b></td><td align="center">·</td><td align="center">🟠 <b>B</b></td></tr>
<tr><td align="center">🟠 <b>B</b></td><td align="center">·</td><td align="center">🔵 <b>A</b></td></tr>
</tbody>
</table>
<p><b>2 attacking pairs</b><br>🔵 A ↔ A and 🟠 B ↔ B</p>
</td><td valign="top" align="center">
<table aria-label="Three rows and two columns">
<tbody>
<tr><td align="center">🔵 <b>A</b></td><td align="center">🟠 <b>B</b></td></tr>
<tr><td align="center">·</td><td align="center">·</td></tr>
<tr><td align="center">🟠 <b>B</b></td><td align="center">🔵 <b>A</b></td></tr>
</tbody>
</table>
<p><b>2 attacking pairs</b><br>🔵 A ↔ A and 🟠 B ↔ B</p>
</td></tr></tbody>
</table>

So we can count **all possible placements of these rectangles**, then multiply
by two. Overlap is fine: this counts placements, not a tiling of the board.

A smaller `4 × 4` board makes every possible top-left cell easy to see.
The colored dots mark rectangle origins, not knight positions.

<table>
<thead><tr><th>Wide rectangle origins</th><th>Tall rectangle origins</th></tr></thead>
<tbody><tr><td valign="top" align="center">
<table aria-label="Six possible top-left cells for wide rectangles on a four by four board">
<tbody>
<tr><td align="center">🔵</td><td align="center">🔵</td><td align="center">·</td><td align="center">·</td></tr>
<tr><td align="center">🔵</td><td align="center">🔵</td><td align="center">·</td><td align="center">·</td></tr>
<tr><td align="center">🔵</td><td align="center">🔵</td><td align="center">·</td><td align="center">·</td></tr>
<tr><td align="center">·</td><td align="center">·</td><td align="center">·</td><td align="center">·</td></tr>
</tbody>
</table>
<p><b>(4 − 1)(4 − 2) = 6 placements</b></p>
</td><td valign="top" align="center">
<table aria-label="Six possible top-left cells for tall rectangles on a four by four board">
<tbody>
<tr><td align="center">🟠</td><td align="center">🟠</td><td align="center">🟠</td><td align="center">·</td></tr>
<tr><td align="center">🟠</td><td align="center">🟠</td><td align="center">🟠</td><td align="center">·</td></tr>
<tr><td align="center">·</td><td align="center">·</td><td align="center">·</td><td align="center">·</td></tr>
<tr><td align="center">·</td><td align="center">·</td><td align="center">·</td><td align="center">·</td></tr>
</tbody>
</table>
<p><b>(4 − 2)(4 − 1) = 6 placements</b></p>
</td></tr></tbody>
</table>

<p align="center"><b>(6 wide + 6 tall) × 2 pairs each = 24 attacking pairs</b></p>

For a general `i × i` board:

- A `2 × 3` rectangle has `i − 1` starting rows and `i − 2` starting columns.
- A `3 × 2` rectangle has `i − 2` starting rows and `i − 1` starting columns.
- Each placement gives two attacking pairs.

```text
attacking pairs = 2(i − 1)(i − 2) + 2(i − 2)(i − 1)
                = 4(i − 1)(i − 2)
```

There is no double-counting here: each attacking pair determines exactly one
bounding rectangle. Back on the `6 × 6` board, that gives
`4 × 5 × 4 = 80` attacking pairs again.

## Why the two approaches are the same

My first solution groups the attacks by **the row they start from**. The refined
solution groups them by **the shape of their bounding rectangle**.

We can connect the two counts without even expanding the expressions:

```text
Down one row:  (i − 1) rows × 2(i − 2) pairs per row
Down two rows: (i − 2) rows × 2(i − 1) pairs per row

Total = 2(i − 1)(i − 2) + 2(i − 2)(i − 1)
      = 4(i − 1)(i − 2)
```

The rectangle idea is not a different answer, just a cleaner way to organize
the same pairs.

## What I kept in the code

I kept both functions in [main.cpp](main.cpp):

- `countByRows()` preserves my original counting approach.
- `countByRectangles()` uses the shorter rectangle formula.

`main()` calls the rectangle version. Switching the function call lets us try
the original one; the output still needs just one answer per board size.

Both take **O(1)** time per board and **O(1)** extra space, so printing all `n`
answers takes **O(n)** time. The counts need `long long` because the number of
square pairs can exceed a 32-bit integer. The compact formula also gives zero attacking pairs
for `i = 1` and `i = 2`.
