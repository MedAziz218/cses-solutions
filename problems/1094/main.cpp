#include <iostream>
#include <string>
#include <vector>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long res=0,last,x;
    cin >> n;
    cin >> last; 
    while (--n){
        cin >> x;
        if (last>x){
            res += last - x;
        }else{
            last = x;
        }
    }
    cout << res;
    return 0;
}