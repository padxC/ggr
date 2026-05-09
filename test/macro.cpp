#include <windows.h>
#include <random>
#include <thread>
#include <atomic>

HHOOK keyboardHook;

// Thread-safe flags
std::atomic<bool> spamming(false);
std::atomic<bool> running(true);

// =======================
// CHANGE SPAM KEY HERE
// =======================
WORD KEY_SPAM = 'G';
// WORD KEY_SPAM = VK_LCONTROL;   // Left Control
// WORD KEY_SPAM = VK_RCONTROL;   // Right Control
// WORD KEY_SPAM = VK_SPACE;      // Spacebar
// WORD KEY_SPAM = VK_RETURN;     // Enter
// WORD KEY_SPAM = VK_TAB;        // Tab
// WORD KEY_SPAM = 'H';           // H key
// WORD KEY_SPAM = 'A';           // A key
// WORD KEY_SPAM = VK_F1;         // F1 key
// WORD KEY_SPAM = VK_SHIFT;      // Shift key
// WORD KEY_SPAM = VK_MENU;       // Alt key

// Random generator (30–40ms)
std::random_device rd;
std::mt19937 gen(rd());
std::uniform_int_distribution<> dist(31.5, 39);

// =======================
// SEND KEY FUNCTION
// =======================
void SendKey()
{
    INPUT input = { 0 };
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = KEY_SPAM;

    // Random delay before press
    Sleep(dist(gen));
    SendInput(1, &input, sizeof(INPUT));

    // Random delay before release
    Sleep(dist(gen));
    input.ki.dwFlags = KEYEVENTF_KEYUP;
    SendInput(1, &input, sizeof(INPUT));
}

// =======================
// SPAM THREAD
// =======================
void SpamThread()
{
    while (running)
    {
        if (spamming)
        {
            SendKey();
        }
        else
        {
            Sleep(1); // reduce CPU usage
        }
    }
}

// =======================
// KEYBOARD HOOK
// =======================
LRESULT CALLBACK KeyboardProc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode >= 0)
    {
        KBDLLHOOKSTRUCT* pKeyBoard = (KBDLLHOOKSTRUCT*)lParam;

        // ESC to exit program
        if (pKeyBoard->vkCode == VK_ESCAPE &&
            (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN))
        {
            running = false;
            PostQuitMessage(0);
            return 1;
        }

        // ` key to hold spam
        if (pKeyBoard->vkCode == VK_OEM_3)
        {
            if (wParam == WM_KEYDOWN)
            {
                spamming = true;
                return 1; // block key
            }
            else if (wParam == WM_KEYUP)
            {
                spamming = false;
                return 1; // block key
            }
        }
    }

    return CallNextHookEx(keyboardHook, nCode, wParam, lParam);
}

// =======================
// MAIN
// =======================
int main()
{
    ShowWindow(GetConsoleWindow(), SW_HIDE);

    keyboardHook = SetWindowsHookEx(
        WH_KEYBOARD_LL,
        KeyboardProc,
        GetModuleHandle(NULL),
        0);

    if (!keyboardHook)
        return 1;

    // Start spam thread
    std::thread worker(SpamThread);

    MSG msg;
    while (running && GetMessage(&msg, NULL, 0, 0))
    {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    running = false;
    worker.join();

    UnhookWindowsHookEx(keyboardHook);
    return 0;
}