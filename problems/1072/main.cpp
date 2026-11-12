#include <iostream>

using namespace std;

// Original approach: count attacks from each row toward lower rows.
long long countByRows(long long side) {
    long long squares = side * side;
    long long total = squares * (squares - 1) / 2;
    if (side < 3) return total;
    long long firstRows = (10 + 4 * (side - 4)) * (side - 2);
    long long penultimateRow = 4 + 2 * (side - 4);
    return total - firstRows - penultimateRow;
}

// Refined approach: each 2x3 or 3x2 rectangle has two attacking pairs.
long long countByRectangles(long long side) {
    long long squares = side * side;
    long long total = squares * (squares - 1) / 2;
    long long attacking = 4 * (side - 1) * (side - 2);
    return total - attacking;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    for (int side = 1; side <= n; ++side) {
        cout << countByRectangles(side) << '\n';
        // Alternatively: cout << countByRows(side) << '\n';
    }

    return 0;
}
