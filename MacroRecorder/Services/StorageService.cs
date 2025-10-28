using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using MacroRecorder.Models;

namespace MacroRecorder.Services;

public sealed class StorageService
{
    private static readonly JsonSerializerOptions SerializerOptions = new()
    {
        WriteIndented = true
    };

    public void Save(string path, IEnumerable<EventRecord> records)
    {
        ArgumentNullException.ThrowIfNull(path);
        ArgumentNullException.ThrowIfNull(records);

        var directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrWhiteSpace(directory) && !Directory.Exists(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var json = JsonSerializer.Serialize(records, SerializerOptions);
        File.WriteAllText(path, json);
    }

    public IReadOnlyList<EventRecord> Load(string path)
    {
        ArgumentNullException.ThrowIfNull(path);

        if (!File.Exists(path))
        {
            throw new FileNotFoundException("Macro file not found.", path);
        }

        var json = File.ReadAllText(path);
        var records = JsonSerializer.Deserialize<List<EventRecord>>(json, SerializerOptions);
        if (records is null)
        {
            return Array.Empty<EventRecord>();
        }

        return records.OrderBy(r => r.TimestampMsSinceStart).ToList();
    }
}
