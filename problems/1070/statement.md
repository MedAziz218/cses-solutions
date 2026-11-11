# Permutations

Source: https://cses.fi/problemset/task/1070/

- **Time limit:** 1.00 s

- **Memory limit:** 512 MB

A permutation of integers $1,2,\ldots,n$ is called *beautiful* if there are no adjacent elements whose difference is $1$.

Given $n$, construct a beautiful permutation if such a permutation exists.

## Input

The only input line contains an integer $n$.

## Output

Print a beautiful permutation of integers $1,2,\ldots,n$. If there are several solutions, you may print any of them. If there are no solutions, print "NO SOLUTION".

## Constraints

- $1 \le n \le 10^6$

## Example 1

Input:

```text
5
```

Output:

```text
4 2 5 3 1
```

## Example 2

Input:

```text
3
```

Output:

```text
NO SOLUTION
```
