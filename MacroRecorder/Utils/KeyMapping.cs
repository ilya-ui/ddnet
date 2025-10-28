using System.Windows.Forms;
using System.Windows.Input;
using MacroRecorder.Models;
using WindowsInput.Native;

namespace MacroRecorder.Utils;

public static class KeyMapping
{
    public static MouseButtonKind FromMouseButton(MouseButtons buttons) => buttons switch
    {
        MouseButtons.Left => MouseButtonKind.Left,
        MouseButtons.Right => MouseButtonKind.Right,
        MouseButtons.Middle => MouseButtonKind.Middle,
        MouseButtons.XButton1 => MouseButtonKind.XButton1,
        MouseButtons.XButton2 => MouseButtonKind.XButton2,
        _ => MouseButtonKind.None
    };

    public static VirtualKeyCode ToVirtualKeyCode(int keyCode) => (VirtualKeyCode)keyCode;

    public static uint ToHotkeyModifierFlags(ModifierKeys modifiers)
    {
        const uint MOD_ALT = 0x0001;
        const uint MOD_CONTROL = 0x0002;
        const uint MOD_SHIFT = 0x0004;
        const uint MOD_WIN = 0x0008;

        uint result = 0;

        if (modifiers.HasFlag(ModifierKeys.Alt))
        {
            result |= MOD_ALT;
        }

        if (modifiers.HasFlag(ModifierKeys.Control))
        {
            result |= MOD_CONTROL;
        }

        if (modifiers.HasFlag(ModifierKeys.Shift))
        {
            result |= MOD_SHIFT;
        }

        if (modifiers.HasFlag(ModifierKeys.Windows))
        {
            result |= MOD_WIN;
        }

        return result;
    }

    public static int ToVirtualKey(Key key) => KeyInterop.VirtualKeyFromKey(key);
}
