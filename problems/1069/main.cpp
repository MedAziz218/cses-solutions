#include <iostream>
#include <string>
#include <vector>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string line;
    getline(cin, line);
    int n = line.length();
    int longest_len = 0, current_len = 0;
    // int longest_start = 0, longest_end = 0;
    int current_start = 0, current_end = 0;
    for (int i=0;i<n;i++){
        if ( i==n-1 || line[i] != line[i+1] ){
            current_end = i;
            current_len = current_end - current_start + 1;
            if (current_len > longest_len){
                longest_len = current_len;
                // longest_start = current_start;
                // longest_end = current_end;
            }
            current_start = i+1;
            current_end = i+1;
        }
    }
    cout << longest_len;
    // if we want to print the longest substring
    // cout << line.substr(longest_start,longest_end+1)<<'\n';
    return 0;
}
