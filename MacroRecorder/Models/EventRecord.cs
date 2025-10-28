using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Windows.Forms;

namespace MacroRecorder.Models;

public enum EventType
{
    MouseMove,
    MouseDown,
    MouseUp,
    MouseWheel,
    KeyDown,
    KeyUp
}

public enum MouseButtonKind
{
    None,
    Left,
    Right,
    Middle,
    XButton1,
    XButton2
}

[JsonConverter(typeof(EventRecordJsonConverter))]
public sealed class EventRecord
{
    public EventType Type { get; set; }

    public long TimestampMsSinceStart { get; set; }

    public EventData Data { get; set; } = null!;

    [JsonIgnore]
    public string Description => Type switch
    {
        EventType.MouseMove => Data is MouseEventData mouse ? $"Move to ({mouse.X}, {mouse.Y})" : "Mouse move",
        EventType.MouseDown => Data is MouseEventData mouse ? $"{mouse.Button} down at ({mouse.X}, {mouse.Y})" : "Mouse down",
        EventType.MouseUp => Data is MouseEventData mouse ? $"{mouse.Button} up at ({mouse.X}, {mouse.Y})" : "Mouse up",
        EventType.MouseWheel => Data is MouseEventData mouse ? $"Wheel {mouse.WheelDelta} at ({mouse.X}, {mouse.Y})" : "Mouse wheel",
        EventType.KeyDown => Data is KeyboardEventData key ? $"Key down {(System.Windows.Forms.Keys)key.KeyCode}" : "Key down",
        EventType.KeyUp => Data is KeyboardEventData key ? $"Key up {(System.Windows.Forms.Keys)key.KeyCode}" : "Key up",
        _ => string.Empty
    };
}

public abstract class EventData
{
}

public sealed class MouseEventData : EventData
{
    public int X { get; set; }

    public int Y { get; set; }

    public MouseButtonKind Button { get; set; } = MouseButtonKind.None;

    public int WheelDelta { get; set; }
}

public sealed class KeyboardEventData : EventData
{
    public int KeyCode { get; set; }

    public bool IsDown { get; set; }
}

public sealed class EventRecordJsonConverter : JsonConverter<EventRecord>
{
    public override EventRecord? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException("Expected start of object when deserializing EventRecord.");
        }

        EventType? type = null;
        long? timestamp = null;
        JsonElement? dataElement = null;

        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndObject)
            {
                break;
            }

            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException("Expected property name while parsing EventRecord.");
            }

            var propertyName = reader.GetString();
            reader.Read();

            switch (propertyName)
            {
                case "type":
                    if (reader.TokenType == JsonTokenType.String)
                    {
                        var typeString = reader.GetString();
                        if (!Enum.TryParse<EventType>(typeString, ignoreCase: true, out var parsedType))
                        {
                            throw new JsonException($"Unsupported event type '{typeString}'.");
                        }

                        type = parsedType;
                    }
                    else if (reader.TokenType == JsonTokenType.Number)
                    {
                        type = (EventType)reader.GetInt32();
                    }
                    else
                    {
                        throw new JsonException("EventRecord.type must be string or number.");
                    }

                    break;
                case "timestampMsSinceStart":
                    timestamp = reader.GetInt64();
                    break;
                case "data":
                    dataElement = JsonDocument.ParseValue(ref reader).RootElement;
                    break;
                default:
                    reader.Skip();
                    break;
            }
        }

        if (type is null)
        {
            throw new JsonException("Missing event type.");
        }

        if (timestamp is null)
        {
            throw new JsonException("Missing timestampMsSinceStart.");
        }

        if (dataElement is null)
        {
            throw new JsonException("Missing data section for event record.");
        }

        var record = new EventRecord
        {
            Type = type.Value,
            TimestampMsSinceStart = timestamp.Value,
            Data = DeserializeData(type.Value, dataElement.Value)
        };

        return record;
    }

    public override void Write(Utf8JsonWriter writer, EventRecord value, JsonSerializerOptions options)
    {
        writer.WriteStartObject();
        writer.WriteString("type", value.Type.ToString());
        writer.WriteNumber("timestampMsSinceStart", value.TimestampMsSinceStart);
        writer.WritePropertyName("data");
        WriteData(writer, value);
        writer.WriteEndObject();
    }

    private static EventData DeserializeData(EventType type, JsonElement element)
    {
        return type switch
        {
            EventType.MouseMove => DeserializeMouse(element, includeWheel: false),
            EventType.MouseDown => DeserializeMouse(element, includeWheel: false),
            EventType.MouseUp => DeserializeMouse(element, includeWheel: false),
            EventType.MouseWheel => DeserializeMouse(element, includeWheel: true),
            EventType.KeyDown => DeserializeKeyboard(element),
            EventType.KeyUp => DeserializeKeyboard(element),
            _ => throw new JsonException($"Unsupported event type '{type}'.")
        };
    }

    private static EventData DeserializeMouse(JsonElement element, bool includeWheel)
    {
        var data = new MouseEventData
        {
            X = element.GetProperty("x").GetInt32(),
            Y = element.GetProperty("y").GetInt32()
        };

        if (element.TryGetProperty("button", out var buttonProperty))
        {
            if (buttonProperty.ValueKind == JsonValueKind.String)
            {
                var buttonString = buttonProperty.GetString();
                if (!Enum.TryParse(buttonString, ignoreCase: true, out MouseButtonKind button))
                {
                    button = MouseButtonKind.None;
                }

                data.Button = button;
            }
            else if (buttonProperty.ValueKind == JsonValueKind.Number)
            {
                data.Button = (MouseButtonKind)buttonProperty.GetInt32();
            }
        }

        if (includeWheel && element.TryGetProperty("wheelDelta", out var wheelProperty))
        {
            data.WheelDelta = wheelProperty.GetInt32();
        }

        return data;
    }

    private static EventData DeserializeKeyboard(JsonElement element)
    {
        return new KeyboardEventData
        {
            KeyCode = element.GetProperty("keyCode").GetInt32(),
            IsDown = element.GetProperty("isDown").GetBoolean()
        };
    }

    private static void WriteData(Utf8JsonWriter writer, EventRecord record)
    {
        writer.WriteStartObject();

        switch (record.Type)
        {
            case EventType.MouseMove:
            case EventType.MouseDown:
            case EventType.MouseUp:
            case EventType.MouseWheel:
                var mouse = record.Data as MouseEventData ?? throw new JsonException("Mouse event missing mouse data.");
                writer.WriteNumber("x", mouse.X);
                writer.WriteNumber("y", mouse.Y);

                if (mouse.Button != MouseButtonKind.None && record.Type != EventType.MouseWheel)
                {
                    writer.WriteString("button", mouse.Button.ToString());
                }

                if (record.Type == EventType.MouseWheel)
                {
                    writer.WriteNumber("wheelDelta", mouse.WheelDelta);
                }

                break;
            case EventType.KeyDown:
            case EventType.KeyUp:
                var keyboard = record.Data as KeyboardEventData ?? throw new JsonException("Keyboard event missing keyboard data.");
                writer.WriteNumber("keyCode", keyboard.KeyCode);
                writer.WriteBoolean("isDown", keyboard.IsDown);
                break;
            default:
                throw new JsonException($"Unsupported event type '{record.Type}'.");
        }

        writer.WriteEndObject();
    }
}
