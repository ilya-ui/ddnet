using System;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using Gma.System.MouseKeyHook;
using MacroRecorder.Models;
using MacroRecorder.Utils;

namespace MacroRecorder.Services;

public sealed class HookService : IDisposable
{
    private const int MouseMoveDebounceMilliseconds = 5;

    private IKeyboardMouseEvents? _globalHook;
    private readonly Stopwatch _stopwatch = new();
    private bool _isRecording;
    private long _lastMoveTimestamp = -1;
    private Point _lastMovePoint;

    public event Action<EventRecord>? EventCaptured;

    public bool IsRecording => _isRecording;

    public void Start()
    {
        if (_isRecording)
        {
            return;
        }

        _globalHook = Hook.GlobalEvents();
        _globalHook.MouseMoveExt += OnMouseMove;
        _globalHook.MouseDownExt += OnMouseDown;
        _globalHook.MouseUpExt += OnMouseUp;
        _globalHook.MouseWheelExt += OnMouseWheel;
        _globalHook.KeyDown += OnKeyDown;
        _globalHook.KeyUp += OnKeyUp;

        _stopwatch.Restart();
        _isRecording = true;
        _lastMoveTimestamp = -1;
    }

    public void Stop()
    {
        if (!_isRecording)
        {
            return;
        }

        _isRecording = false;
        _stopwatch.Stop();
        _lastMoveTimestamp = -1;
        _lastMovePoint = Point.Empty;

        if (_globalHook is not null)
        {
            _globalHook.MouseMoveExt -= OnMouseMove;
            _globalHook.MouseDownExt -= OnMouseDown;
            _globalHook.MouseUpExt -= OnMouseUp;
            _globalHook.MouseWheelExt -= OnMouseWheel;
            _globalHook.KeyDown -= OnKeyDown;
            _globalHook.KeyUp -= OnKeyUp;
            _globalHook.Dispose();
            _globalHook = null;
        }
    }

    public void Dispose()
    {
        Stop();
    }

    private void OnMouseMove(object? sender, MouseEventExtArgs e)
    {
        if (!ShouldProcessMouseEvent(e))
        {
            return;
        }

        var timestamp = _stopwatch.ElapsedMilliseconds;
        var point = e.Location;

        if (_lastMoveTimestamp >= 0 && timestamp - _lastMoveTimestamp < MouseMoveDebounceMilliseconds && point == _lastMovePoint)
        {
            return;
        }

        _lastMoveTimestamp = timestamp;
        _lastMovePoint = point;

        EmitEvent(EventType.MouseMove, timestamp, new MouseEventData
        {
            X = point.X,
            Y = point.Y
        });
    }

    private void OnMouseDown(object? sender, MouseEventExtArgs e)
    {
        if (!ShouldProcessMouseEvent(e))
        {
            return;
        }

        EmitEvent(EventType.MouseDown, _stopwatch.ElapsedMilliseconds, new MouseEventData
        {
            X = e.Location.X,
            Y = e.Location.Y,
            Button = KeyMapping.FromMouseButton(e.Button)
        });
    }

    private void OnMouseUp(object? sender, MouseEventExtArgs e)
    {
        if (!ShouldProcessMouseEvent(e))
        {
            return;
        }

        EmitEvent(EventType.MouseUp, _stopwatch.ElapsedMilliseconds, new MouseEventData
        {
            X = e.Location.X,
            Y = e.Location.Y,
            Button = KeyMapping.FromMouseButton(e.Button)
        });
    }

    private void OnMouseWheel(object? sender, MouseEventExtArgs e)
    {
        if (!ShouldProcessMouseEvent(e))
        {
            return;
        }

        EmitEvent(EventType.MouseWheel, _stopwatch.ElapsedMilliseconds, new MouseEventData
        {
            X = e.Location.X,
            Y = e.Location.Y,
            WheelDelta = e.Delta
        });
    }

    private void OnKeyDown(object? sender, KeyEventArgs e)
    {
        if (!ShouldProcessKeyEvent(e))
        {
            return;
        }

        EmitEvent(EventType.KeyDown, _stopwatch.ElapsedMilliseconds, new KeyboardEventData
        {
            KeyCode = (int)e.KeyCode,
            IsDown = true
        });
    }

    private void OnKeyUp(object? sender, KeyEventArgs e)
    {
        if (!ShouldProcessKeyEvent(e))
        {
            return;
        }

        EmitEvent(EventType.KeyUp, _stopwatch.ElapsedMilliseconds, new KeyboardEventData
        {
            KeyCode = (int)e.KeyCode,
            IsDown = false
        });
    }

    private bool ShouldProcessMouseEvent(MouseEventExtArgs e)
    {
        return _isRecording && !e.IsInjected;
    }

    private bool ShouldProcessKeyEvent(KeyEventArgs e)
    {
        if (!_isRecording)
        {
            return false;
        }

        if (e is KeyEventArgsExt ext)
        {
            return !ext.IsInjected;
        }

        return true;
    }

    private void EmitEvent(EventType type, long timestamp, EventData data)
    {
        if (!_isRecording)
        {
            return;
        }

        var record = new EventRecord
        {
            Type = type,
            TimestampMsSinceStart = timestamp,
            Data = data
        };

        EventCaptured?.Invoke(record);
    }
}
