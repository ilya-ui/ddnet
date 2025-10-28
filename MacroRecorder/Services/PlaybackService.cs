using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using MacroRecorder.Models;
using MacroRecorder.Utils;
using WindowsInput;
using WindowsInput.Native;

namespace MacroRecorder.Services;

public sealed class PlaybackService : IDisposable
{
    private readonly InputSimulator _inputSimulator = new();
    private CancellationTokenSource? _playbackCts;
    private Task? _playbackTask;

    public event EventHandler? PlaybackCompleted;

    public bool IsPlaying => _playbackTask is { IsCompleted: false };

    public Task StartAsync(IReadOnlyList<EventRecord> events, double speedMultiplier, int repeatCount)
    {
        if (events is null)
        {
            throw new ArgumentNullException(nameof(events));
        }

        if (events.Count == 0)
        {
            throw new ArgumentException("No events to play back.", nameof(events));
        }

        if (IsPlaying)
        {
            throw new InvalidOperationException("Playback is already running.");
        }

        if (speedMultiplier <= 0)
        {
            speedMultiplier = 1.0;
        }

        _playbackCts = new CancellationTokenSource();
        var token = _playbackCts.Token;

        _playbackTask = Task.Run(() => PlayInternalAsync(events, speedMultiplier, repeatCount, token), token);
        _ = _playbackTask.ContinueWith(_ => OnPlaybackCompleted(), CancellationToken.None, TaskContinuationOptions.None, TaskScheduler.Default);

        return _playbackTask;
    }

    public void Stop()
    {
        if (_playbackCts is null)
        {
            return;
        }

        if (!_playbackCts.IsCancellationRequested)
        {
            _playbackCts.Cancel();
        }
    }

    private async Task PlayInternalAsync(IReadOnlyList<EventRecord> events, double speedMultiplier, int repeatCount, CancellationToken token)
    {
        try
        {
            var infinite = repeatCount <= 0;
            var iteration = 0;

            while (infinite || iteration < repeatCount)
            {
                iteration++;

                long previousTimestamp = 0;

                foreach (var record in events)
                {
                    token.ThrowIfCancellationRequested();

                    var delay = record.TimestampMsSinceStart - previousTimestamp;
                    previousTimestamp = record.TimestampMsSinceStart;

                    if (delay > 0)
                    {
                        var scaledDelay = (int)Math.Round(delay / speedMultiplier);
                        if (scaledDelay > 0)
                        {
                            await Task.Delay(scaledDelay, token);
                        }
                    }

                    token.ThrowIfCancellationRequested();
                    ExecuteRecord(record);
                }
            }
        }
        catch (OperationCanceledException)
        {
            // Expected during cancellation. Swallow to allow graceful completion.
        }
        finally
        {
            CleanupPlaybackState();
        }
    }

    private void ExecuteRecord(EventRecord record)
    {
        switch (record.Type)
        {
            case EventType.MouseMove:
                if (record.Data is MouseEventData moveData)
                {
                    MoveMouse(moveData.X, moveData.Y);
                }
                break;
            case EventType.MouseDown:
                if (record.Data is MouseEventData downData)
                {
                    MoveMouse(downData.X, downData.Y);
                    MouseButtonDown(downData.Button);
                }
                break;
            case EventType.MouseUp:
                if (record.Data is MouseEventData upData)
                {
                    MoveMouse(upData.X, upData.Y);
                    MouseButtonUp(upData.Button);
                }
                break;
            case EventType.MouseWheel:
                if (record.Data is MouseEventData wheelData)
                {
                    MoveMouse(wheelData.X, wheelData.Y);
                    MouseWheel(wheelData.WheelDelta);
                }
                break;
            case EventType.KeyDown:
                if (record.Data is KeyboardEventData keyDown)
                {
                    var key = KeyMapping.ToVirtualKeyCode(keyDown.KeyCode);
                    _inputSimulator.Keyboard.KeyDown(key);
                }
                break;
            case EventType.KeyUp:
                if (record.Data is KeyboardEventData keyUp)
                {
                    var key = KeyMapping.ToVirtualKeyCode(keyUp.KeyCode);
                    _inputSimulator.Keyboard.KeyUp(key);
                }
                break;
        }
    }

    private void MoveMouse(int x, int y)
    {
        var screen = SystemInformation.VirtualScreen;
        var normalizedX = NormalizeCoordinate(x, screen.Left, screen.Width);
        var normalizedY = NormalizeCoordinate(y, screen.Top, screen.Height);
        _inputSimulator.Mouse.MoveMouseToPositionOnVirtualDesktop(normalizedX, normalizedY);
    }

    private static double NormalizeCoordinate(int value, int origin, int size)
    {
        if (size <= 0)
        {
            return 0;
        }

        var relative = (value - origin) / (double)size;
        var normalized = relative * 65535.0;
        return Math.Clamp(normalized, 0, 65535);
    }

    private void MouseButtonDown(MouseButtonKind button)
    {
        switch (button)
        {
            case MouseButtonKind.Left:
                _inputSimulator.Mouse.LeftButtonDown();
                break;
            case MouseButtonKind.Right:
                _inputSimulator.Mouse.RightButtonDown();
                break;
            case MouseButtonKind.Middle:
                _inputSimulator.Mouse.MiddleButtonDown();
                break;
            case MouseButtonKind.XButton1:
                _inputSimulator.Mouse.XButtonDown(1);
                break;
            case MouseButtonKind.XButton2:
                _inputSimulator.Mouse.XButtonDown(2);
                break;
        }
    }

    private void MouseButtonUp(MouseButtonKind button)
    {
        switch (button)
        {
            case MouseButtonKind.Left:
                _inputSimulator.Mouse.LeftButtonUp();
                break;
            case MouseButtonKind.Right:
                _inputSimulator.Mouse.RightButtonUp();
                break;
            case MouseButtonKind.Middle:
                _inputSimulator.Mouse.MiddleButtonUp();
                break;
            case MouseButtonKind.XButton1:
                _inputSimulator.Mouse.XButtonUp(1);
                break;
            case MouseButtonKind.XButton2:
                _inputSimulator.Mouse.XButtonUp(2);
                break;
        }
    }

    private void MouseWheel(int delta)
    {
        if (delta == 0)
        {
            return;
        }

        var steps = (int)Math.Round(delta / 120.0);
        if (steps != 0)
        {
            _inputSimulator.Mouse.VerticalScroll(steps);
        }
    }

    private void CleanupPlaybackState()
    {
        var cts = _playbackCts;
        _playbackCts = null;
        cts?.Dispose();

        _playbackTask = null;
    }

    private void OnPlaybackCompleted()
    {
        PlaybackCompleted?.Invoke(this, EventArgs.Empty);
    }

    public void Dispose()
    {
        Stop();
    }
}
