#include <Windows.h>
#include <iostream>
#include <map>

HHOOK g_hKeyboardHook = NULL;
std::map<DWORD, bool> g_keyState;

// Function to simulate key press
void SimulateKeyPress(WORD vkCode) {
    INPUT inputs[2] = {};
    
    // Key down
    inputs[0].type = INPUT_KEYBOARD;
    inputs[0].ki.wVk = vkCode;
    
    // Key up
    inputs[1].type = INPUT_KEYBOARD;
    inputs[1].ki.wVk = vkCode;
    inputs[1].ki.dwFlags = KEYEVENTF_KEYUP;
    
    SendInput(2, inputs, sizeof(INPUT));
}

LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam) {
    // CRITICAL: Always pass the event if nCode < 0 [citation:1]
    if (nCode < 0) {
        return CallNextHookEx(g_hKeyboardHook, nCode, wParam, lParam);
    }
    
    if (nCode == HC_ACTION) {
        KBDLLHOOKSTRUCT* pKeyStruct = (KBDLLHOOKSTRUCT*)lParam;
        
        // KEY FIX: Check if this is an injected event (from SendInput)
        // If it's injected, let it pass through immediately [citation:1][citation:4]
        if (pKeyStruct->flags & LLKHF_INJECTED) {
            return CallNextHookEx(g_hKeyboardHook, nCode, wParam, lParam);
        }
        
        // Now handle real user input
        if (pKeyStruct->vkCode == VK_F1) {
            // Handle key down
            if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
                if (!g_keyState[pKeyStruct->vkCode]) {
                    g_keyState[pKeyStruct->vkCode] = true;
                    
                    std::cout << "F1 pressed - Sending 'I' key" << std::endl;
                    
                    // Simulate 'I' key press
                    SimulateKeyPress('I');
                    
                    // Block the original F1 key
                    return 1;
                }
            }
            // Handle key up
            else if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
                g_keyState[pKeyStruct->vkCode] = false;
                return 1; // Block F1 key up too
            }
        }
        else {
            // For other keys, update state on key up
            if (wParam == WM_KEYUP || wParam == WM_SYSKEYUP) {
                g_keyState[pKeyStruct->vkCode] = false;
            }
        }
    }
    
    return CallNextHookEx(g_hKeyboardHook, nCode, wParam, lParam);
}

int main() {
    std::cout << "F1 to I Remapper (Fixed Version)" << std::endl;
    std::cout << "==================================" << std::endl;
    std::cout << "F1 key will now type 'I'" << std::endl;
    std::cout << "Press Ctrl+C in console to exit" << std::endl;
    std::cout << std::endl;
    
    // Install the low-level keyboard hook
    g_hKeyboardHook = SetWindowsHookEx(WH_KEYBOARD_LL, 
                                       LowLevelKeyboardProc, 
                                       GetModuleHandle(NULL), 
                                       0);
    
    if (g_hKeyboardHook == NULL) {
        std::cerr << "Failed to install keyboard hook! Error: " << GetLastError() << std::endl;
        std::cout << "Try running as Administrator" << std::endl;
        system("pause");
        return 1;
    }
    
    std::cout << "Hook installed successfully!" << std::endl;
    std::cout << std::endl;
    
    // Message loop
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    
    UnhookWindowsHookEx(g_hKeyboardHook);
    return 0;
}