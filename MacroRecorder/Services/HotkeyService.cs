using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using MacroRecorder.Utils;

namespace MacroRecorder.Services;

public sealed class HotkeyService : IDisposable
{
    private const int WmHotKey = 0x0312;

    private readonly HwndSource _source;
    private readonly Dictionary<int, Action> _handlers = new();
    private int _currentId;

    public HotkeyService(Window window)
    {
        ArgumentNullException.ThrowIfNull(window);

        var helper = new WindowInteropHelper(window);
        var handle = helper.Handle;
        if (handle == IntPtr.Zero)
        {
            throw new InvalidOperationException("The window handle is not yet created. Create HotkeyService after SourceInitialized.");
        }

        _source = HwndSource.FromHwnd(handle) ?? throw new InvalidOperationException("Unable to acquire window source for hotkey registration.");
        _source.AddHook(WndProc);
    }

    public int RegisterHotKey(ModifierKeys modifiers, Key key, Action callback)
    {
        ArgumentNullException.ThrowIfNull(callback);

        _currentId++;
        var id = _currentId;
        var modifierFlags = KeyMapping.ToHotkeyModifierFlags(modifiers);
        var virtualKey = KeyMapping.ToVirtualKey(key);

        if (!NativeMethods.RegisterHotKey(_source.Handle, id, modifierFlags, virtualKey))
        {
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Failed to register global hotkey.");
        }

        _handlers[id] = callback;
        return id;
    }

    public void UnregisterHotKey(int id)
    {
        if (_handlers.Remove(id))
        {
            NativeMethods.UnregisterHotKey(_source.Handle, id);
        }
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == WmHotKey)
        {
            var id = wParam.ToInt32();
            if (_handlers.TryGetValue(id, out var callback))
            {
                callback();
                handled = true;
            }
        }

        return IntPtr.Zero;
    }

    public void Dispose()
    {
        foreach (var id in _handlers.Keys.ToList())
        {
            NativeMethods.UnregisterHotKey(_source.Handle, id);
        }

        _handlers.Clear();
        _source.RemoveHook(WndProc);
    }

    private static class NativeMethods
    {
        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, int vk);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool UnregisterHotKey(IntPtr hWnd, int id);
    }
}
