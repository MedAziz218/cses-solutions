#include <iostream>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n,x,t;
    cin >> n;
    t = n*(n+1)/2;
    while(--n) {cin >> x; t-=x;};
    cout << t;
    return 0;
}
