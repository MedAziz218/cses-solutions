#include <algorithm>
#include <iostream>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;

    while (t--) {
        long long y, x;
        cin >> y >> x;

        long long k = max(x, y);
        long long diagonal = k * k - k + 1;
        long long res = diagonal + (k % 2 ? x - y : y - x);
        cout << res << '\n';
    }

    return 0;
}
