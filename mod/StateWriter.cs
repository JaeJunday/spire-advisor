using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace SpireAdvisor;

internal static class StateWriter
{
    static readonly string Dir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "SlayTheSpire2", "spire-advisor");

    // macOS에서 ApplicationData는 ~/.config라서, 실제 세이브 옆으로 고정해요.
    static string MacDir => "/Users/jaejun/Library/Application Support/SlayTheSpire2/spire-advisor";

    public static string LivePath => Path.Combine(MacDir, "live.json");
    public static string LogPath => Path.Combine(MacDir, "mod.log");

    static string ResolveDir()
    {
        try
        {
            if (Directory.Exists("/Users/jaejun/Library/Application Support/SlayTheSpire2"))
                return MacDir;
        }
        catch { }
        return Dir;
    }

    public static void Write(Dictionary<string, object> fields)
    {
        try
        {
            var dir = ResolveDir();
            Directory.CreateDirectory(dir);
            fields["mtime"] = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            var json = JsonSerializer.Serialize(fields);
            var path = Path.Combine(dir, "live.json");
            var tmp = path + ".tmp";
            File.WriteAllText(tmp, json);
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmp, path);
        }
        catch (Exception ex) { Trace("write: " + ex.Message); }
    }

    public static void Touch(string screen)
    {
        Write(new Dictionary<string, object> { ["screen"] = screen });
    }

    public static void Trace(string msg)
    {
        try
        {
            var dir = ResolveDir();
            Directory.CreateDirectory(dir);
            File.AppendAllText(Path.Combine(dir, "mod.log"), DateTime.UtcNow.ToString("o") + " " + msg + "\n");
        }
        catch { }
    }
}
