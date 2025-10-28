using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using MacroRecorder.Models;
using MacroRecorder.Services;
using Microsoft.Win32;

namespace MacroRecorder;

public partial class MainWindow : Window
{
    private readonly ObservableCollection<EventRecord> _records = new();
    private readonly HookService _hookService = new();
    private readonly PlaybackService _playbackService = new();
    private readonly StorageService _storageService = new();
    private HotkeyService? _hotkeyService;

    private bool _isRecording;
    private bool _isStoppingPlayback;

    private enum ActivityState
    {
        Idle,
        Recording,
        Playing,
        Stopping
    }

    public MainWindow()
    {
        InitializeComponent();

        EventsGrid.ItemsSource = _records;

        _hookService.EventCaptured += HandleEventCaptured;
        _playbackService.PlaybackCompleted += HandlePlaybackCompleted;

        SourceInitialized += OnSourceInitialized;
        Closing += OnClosing;

        SetStatus(ActivityState.Idle);
        UpdateControlStates();
    }

    private void OnSourceInitialized(object? sender, EventArgs e)
    {
        try
        {
            _hotkeyService = new HotkeyService(this);
            _hotkeyService.RegisterHotKey(ModifierKeys.Control | ModifierKeys.Shift, Key.R, ToggleRecordingHotkey);
            _hotkeyService.RegisterHotKey(ModifierKeys.Control | ModifierKeys.Shift, Key.P, StartPlaybackHotkey);
            _hotkeyService.RegisterHotKey(ModifierKeys.Control | ModifierKeys.Shift, Key.S, StopHotkey);
        }
        catch (Exception ex)
        {
            ShowError($"Failed to register global hotkeys: {ex.Message}");
        }
    }

    private void ToggleRecordingHotkey()
    {
        Dispatcher.Invoke(() =>
        {
            if (_isRecording)
            {
                StopRecording();
            }
            else
            {
                StartRecording();
            }
        });
    }

    private void StartPlaybackHotkey()
    {
        Dispatcher.Invoke(StartPlayback);
    }

    private void StopHotkey()
    {
        Dispatcher.Invoke(StopActions);
    }

    private void HandleEventCaptured(EventRecord record)
    {
        Dispatcher.BeginInvoke(new Action(() =>
        {
            _records.Add(record);
            SetStatus(ActivityState.Recording, $"{_records.Count} events");
            UpdateControlStates();
        }));
    }

    private void HandlePlaybackCompleted(object? sender, EventArgs e)
    {
        Dispatcher.BeginInvoke(new Action(() =>
        {
            _isStoppingPlayback = false;
            if (!_isRecording)
            {
                SetStatus(ActivityState.Idle);
            }

            UpdateControlStates();
        }));
    }

    private void OnClosing(object? sender, CancelEventArgs e)
    {
        _hookService.Dispose();
        _playbackService.Dispose();
        _hotkeyService?.Dispose();
    }

    private void StartRecording()
    {
        if (_isRecording)
        {
            return;
        }

        if (_playbackService.IsPlaying)
        {
            _playbackService.Stop();
        }

        _records.Clear();

        try
        {
            _hookService.Start();
            _isRecording = true;
            SetStatus(ActivityState.Recording, "Recording started");
        }
        catch (Exception ex)
        {
            ShowError($"Unable to start recording: {ex.Message}");
            _hookService.Stop();
            _isRecording = false;
            SetStatus(ActivityState.Idle);
        }

        UpdateControlStates();
    }

    private void StopRecording()
    {
        if (!_isRecording)
        {
            return;
        }

        _hookService.Stop();
        _isRecording = false;
        if (!_playbackService.IsPlaying)
        {
            SetStatus(ActivityState.Idle, $"{_records.Count} events recorded");
        }
        UpdateControlStates();
    }

    private void StartPlayback()
    {
        if (_isRecording)
        {
            ShowError("Stop recording before starting playback.");
            return;
        }

        if (_playbackService.IsPlaying)
        {
            return;
        }

        var events = _records.OrderBy(r => r.TimestampMsSinceStart).ToList();
        if (events.Count == 0)
        {
            ShowError("No events to play back. Record or load a macro first.", MessageBoxImage.Information);
            return;
        }

        var speed = ParseSpeedMultiplier();
        var repeat = ParseRepeatCount();

        _isStoppingPlayback = false;

        try
        {
            _playbackService.StartAsync(events, speed, repeat);
            SetStatus(ActivityState.Playing, repeat <= 0 ? $"Speed {speed:0.##}x, infinite" : $"Speed {speed:0.##}x, {repeat} cycles");
            UpdateControlStates();
        }
        catch (Exception ex)
        {
            ShowError($"Unable to start playback: {ex.Message}");
            SetStatus(ActivityState.Idle);
        }
    }

    private void StopPlayback()
    {
        if (!_playbackService.IsPlaying)
        {
            return;
        }

        _playbackService.Stop();
        _isStoppingPlayback = true;
        SetStatus(ActivityState.Stopping);
        UpdateControlStates();
    }

    private void StopActions()
    {
        if (_isRecording)
        {
            StopRecording();
        }
        else if (_playbackService.IsPlaying)
        {
            StopPlayback();
        }
    }

    private void SaveMacro()
    {
        if (_records.Count == 0)
        {
            ShowError("There are no events to save.", MessageBoxImage.Information);
            return;
        }

        var dialog = new SaveFileDialog
        {
            Title = "Save Macro",
            Filter = "Macro files (*.macro.json)|*.macro.json|JSON files (*.json)|*.json|All files (*.*)|*.*",
            DefaultExt = ".macro.json",
            FileName = "Macro.macro.json"
        };

        if (dialog.ShowDialog(this) == true)
        {
            try
            {
                _storageService.Save(dialog.FileName, _records);
                SetStatus(ActivityState.Idle, $"Saved to {Path.GetFileName(dialog.FileName)}");
            }
            catch (Exception ex)
            {
                ShowError($"Failed to save macro: {ex.Message}");
            }
        }
    }

    private void LoadMacro()
    {
        var dialog = new OpenFileDialog
        {
            Title = "Load Macro",
            Filter = "Macro files (*.macro.json)|*.macro.json|JSON files (*.json)|*.json|All files (*.*)|*.*"
        };

        if (dialog.ShowDialog(this) == true)
        {
            try
            {
                var records = _storageService.Load(dialog.FileName);
                _records.Clear();
                foreach (var record in records)
                {
                    _records.Add(record);
                }

                SetStatus(ActivityState.Idle, $"Loaded {_records.Count} events");
                UpdateControlStates();
            }
            catch (Exception ex)
            {
                ShowError($"Failed to load macro: {ex.Message}");
            }
        }
    }

    private double ParseSpeedMultiplier()
    {
        var text = SpeedComboBox.Text?.Trim();
        if (string.IsNullOrWhiteSpace(text))
        {
            return 1.0;
        }

        if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out var value) && value > 0)
        {
            return value;
        }

        if (double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentCulture, out value) && value > 0)
        {
            return value;
        }

        ShowError("Invalid speed multiplier. Using 1.0x by default.", MessageBoxImage.Warning);
        SpeedComboBox.Text = "1";
        return 1.0;
    }

    private int ParseRepeatCount()
    {
        var text = RepeatTextBox.Text?.Trim();
        if (string.IsNullOrWhiteSpace(text))
        {
            return 1;
        }

        if (string.Equals(text, "inf", StringComparison.OrdinalIgnoreCase) || text == "∞")
        {
            return 0;
        }

        if (int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out var value) && value >= 0)
        {
            return value;
        }

        if (int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentCulture, out value) && value >= 0)
        {
            return value;
        }

        ShowError("Invalid repeat count. Using 1 by default.", MessageBoxImage.Warning);
        RepeatTextBox.Text = "1";
        return 1;
    }

    private void UpdateControlStates()
    {
        RecordButton.IsEnabled = !_isRecording && !_isStoppingPlayback;
        StopButton.IsEnabled = _isRecording || _playbackService.IsPlaying || _isStoppingPlayback;
        PlayButton.IsEnabled = !_isRecording && !_playbackService.IsPlaying && _records.Count > 0;
        SaveButton.IsEnabled = _records.Count > 0 && !_isRecording;
        LoadButton.IsEnabled = !_isRecording && !_playbackService.IsPlaying && !_isStoppingPlayback;
    }

    private void SetStatus(ActivityState state, string? details = null)
    {
        var brush = state switch
        {
            ActivityState.Recording => Brushes.IndianRed,
            ActivityState.Playing => Brushes.LightGreen,
            ActivityState.Stopping => Brushes.Goldenrod,
            _ => Brushes.LightGray
        };

        var label = state switch
        {
            ActivityState.Recording => "Status: Recording",
            ActivityState.Playing => "Status: Playing",
            ActivityState.Stopping => "Status: Stopping playback",
            _ => "Status: Idle"
        };

        if (!string.IsNullOrWhiteSpace(details))
        {
            label += $" ({details})";
        }

        StatusLabel.Text = label;
        StatusIndicator.Background = brush;
    }

    private void ShowError(string message, MessageBoxImage image = MessageBoxImage.Error)
    {
        MessageBox.Show(this, message, "Macro Recorder", MessageBoxButton.OK, image);
    }

    private void OnRecordClicked(object sender, RoutedEventArgs e) => StartRecording();

    private void OnStopClicked(object sender, RoutedEventArgs e) => StopActions();

    private void OnPlayClicked(object sender, RoutedEventArgs e) => StartPlayback();

    private void OnSaveClicked(object sender, RoutedEventArgs e) => SaveMacro();

    private void OnLoadClicked(object sender, RoutedEventArgs e) => LoadMacro();
}
