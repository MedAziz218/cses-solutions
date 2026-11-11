#include <iostream>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n;
    cin >> n;
    cout << n;
    while (n != 1){ 
        n%2==0 ? (n/=2) : (n=3*n+1);
        cout << ' ' << n ;
    }
    cout << '\n';
    return 0;
}
