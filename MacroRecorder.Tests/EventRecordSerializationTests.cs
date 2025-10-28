using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using MacroRecorder.Models;
using MacroRecorder.Services;
using Xunit;

namespace MacroRecorder.Tests;

public class EventRecordSerializationTests
{
    [Fact]
    public void SerializeAndDeserialize_PreservesEventData()
    {
        var records = new List<EventRecord>
        {
            new()
            {
                Type = EventType.MouseMove,
                TimestampMsSinceStart = 0,
                Data = new MouseEventData { X = 100, Y = 200 }
            },
            new()
            {
                Type = EventType.MouseDown,
                TimestampMsSinceStart = 15,
                Data = new MouseEventData { X = 100, Y = 200, Button = MouseButtonKind.Left }
            },
            new()
            {
                Type = EventType.MouseWheel,
                TimestampMsSinceStart = 42,
                Data = new MouseEventData { X = 120, Y = 240, WheelDelta = 120 }
            },
            new()
            {
                Type = EventType.KeyDown,
                TimestampMsSinceStart = 55,
                Data = new KeyboardEventData { KeyCode = 0x41, IsDown = true }
            },
            new()
            {
                Type = EventType.KeyUp,
                TimestampMsSinceStart = 80,
                Data = new KeyboardEventData { KeyCode = 0x41, IsDown = false }
            }
        };

        var options = new JsonSerializerOptions { WriteIndented = true };
        var json = JsonSerializer.Serialize(records, options);
        var restored = JsonSerializer.Deserialize<List<EventRecord>>(json, options);

        Assert.NotNull(restored);
        Assert.Equal(records.Count, restored!.Count);

        for (var i = 0; i < records.Count; i++)
        {
            AssertEquivalent(records[i], restored[i]);
        }
    }

    [Fact]
    public void StorageService_SaveAndLoad_RoundTripsSuccessfully()
    {
        var storage = new StorageService();
        var records = new List<EventRecord>
        {
            new()
            {
                Type = EventType.MouseMove,
                TimestampMsSinceStart = 5,
                Data = new MouseEventData { X = 10, Y = 20 }
            },
            new()
            {
                Type = EventType.MouseUp,
                TimestampMsSinceStart = 20,
                Data = new MouseEventData { X = 10, Y = 20, Button = MouseButtonKind.Right }
            },
            new()
            {
                Type = EventType.KeyDown,
                TimestampMsSinceStart = 30,
                Data = new KeyboardEventData { KeyCode = 0x70, IsDown = true }
            }
        };

        var path = Path.Combine(Path.GetTempPath(), $"macro_{Guid.NewGuid():N}.macro.json");

        try
        {
            storage.Save(path, records);
            var loaded = storage.Load(path);

            Assert.Equal(records.Count, loaded.Count);
            for (var i = 0; i < records.Count; i++)
            {
                AssertEquivalent(records[i], loaded[i]);
            }
        }
        finally
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
    }

    private static void AssertEquivalent(EventRecord expected, EventRecord actual)
    {
        Assert.Equal(expected.Type, actual.Type);
        Assert.Equal(expected.TimestampMsSinceStart, actual.TimestampMsSinceStart);

        switch (expected.Data)
        {
            case MouseEventData expectedMouse:
                var actualMouse = Assert.IsType<MouseEventData>(actual.Data);
                Assert.Equal(expectedMouse.X, actualMouse.X);
                Assert.Equal(expectedMouse.Y, actualMouse.Y);
                Assert.Equal(expectedMouse.Button, actualMouse.Button);
                Assert.Equal(expectedMouse.WheelDelta, actualMouse.WheelDelta);
                break;
            case KeyboardEventData expectedKeyboard:
                var actualKeyboard = Assert.IsType<KeyboardEventData>(actual.Data);
                Assert.Equal(expectedKeyboard.KeyCode, actualKeyboard.KeyCode);
                Assert.Equal(expectedKeyboard.IsDown, actualKeyboard.IsDown);
                break;
            default:
                throw new InvalidOperationException($"Unsupported event data type {expected.Data?.GetType().Name}");
        }
    }
}
